import pytest
import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

async def get_admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.INITIAL_SUPERUSER_USERNAME,
            "password": settings.INITIAL_SUPERUSER_PASSWORD
        }
    )
    assert resp.status_code == 200
    return resp.json()["token"]["access_token"]

@pytest.mark.asyncio
async def test_product_and_bom_lifecycle():
    """测试产品主数据、APQP阶段门与轻量BOM层级 (docs/10 & docs/11)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 查询已种子化的 99824 核心产品
        res = await client.get("/api/v1/products", headers=headers)
        assert res.status_code == 200
        products = res.json()
        assert len(products) >= 1
        prod_99824 = next(p for p in products if p["bravio_id"] == "99824")
        assert prod_99824["kba_approval_number"] == "E1-149R-001234"

        # 2. 推进 APQP 阶段门到量产 SOP
        adv_res = await client.post(
            f"/api/v1/products/{prod_99824['id']}/advance-lifecycle?target_status=MASS_PRODUCTION_SOP",
            headers=headers
        )
        assert adv_res.status_code == 200
        assert adv_res.json()["lifecycle_status"] == "MASS_PRODUCTION_SOP"
        assert adv_res.json()["current_phase_gate"] == 5

        # 3. 查询产品对应的 BOM 树与包装层级
        bom_res = await client.get(f"/api/v1/boms/product/{prod_99824['id']}", headers=headers)
        assert bom_res.status_code == 200
        boms = bom_res.json()
        assert len(boms) >= 1
        bom = boms[0]
        assert len(bom["items"]) >= 4
        assert bom["packaging"]["pieces_per_box"] == 2
        assert bom["packaging"]["boxes_per_carton"] == 20

@pytest.mark.asyncio
async def test_barcode_engine_and_traceability_pairing():
    """测试条码规则引擎生成/逆向解析与双灯Binning配对防呆 (docs/12 & docs/07)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 正向生成 32 位激光码
        gen_res = await client.post(
            "/api/v1/barcode-rules/generate",
            json={
                "level": "SN",
                "bravio_id": "99824",
                "revision": "A",
                "year_week": "2642",
                "sequence": 108,
                "binning": "6000K-1200LM-12V"
            },
            headers=headers
        )
        assert gen_res.status_code == 200
        sn = gen_res.json()["barcode"]
        assert len(sn) == 32
        assert sn.startswith("99824A264200000108")

        # 2. 逆向解析条码
        parse_res = await client.post(
            "/api/v1/barcode-rules/parse",
            json={"barcode": sn},
            headers=headers
        )
        assert parse_res.status_code == 200
        pdata = parse_res.json()
        assert pdata["is_valid"] is True
        assert pdata["level"] == "SN"
        assert pdata["parsed_fields"]["bravio_id"] == "99824"

        # 3. 烧录第一支与第二支具有相同 Binning 的产品，测试一盒双支配对防呆 PASS
        import time
        base_seq = (int(time.time() * 1000) % 800000) + 10000
        sn1_res = await client.post(
            "/api/v1/traceability/laser-codes",
            json={
                "product_id": "mock_p1",
                "bravio_id": "99824",
                "revision": "A",
                "sequence_int": base_seq + 1,
                "color_temp_bin": "6000K",
                "flux_bin": "1200LM",
                "voltage_bin": "12V"
            },
            headers=headers
        )
        assert sn1_res.status_code == 201
        sn1 = sn1_res.json()["serial_number"]

        sn2_res = await client.post(
            "/api/v1/traceability/laser-codes",
            json={
                "product_id": "mock_p1",
                "bravio_id": "99824",
                "revision": "A",
                "sequence_int": base_seq + 2,
                "color_temp_bin": "6000K",
                "flux_bin": "1200LM",
                "voltage_bin": "12V"
            },
            headers=headers
        )
        assert sn2_res.status_code == 201
        sn2 = sn2_res.json()["serial_number"]

        # 执行双灯配对
        pair_res = await client.post(
            "/api/v1/traceability/pairing/check-box",
            json={
                "box_barcode": f"BOX-99824-2642-{base_seq:06d}",
                "sn_first": sn1,
                "sn_second": sn2
            },
            headers=headers
        )
        assert pair_res.status_code == 200
        pair_data = pair_res.json()
        assert pair_data["is_pass"] is True
        assert pair_data["status"] == "MATCHED"

        # 4. 测试不同 Binning 时触发 Poka-Yoke 声光拦截
        sn3_diff_res = await client.post(
            "/api/v1/traceability/laser-codes",
            json={
                "product_id": "mock_p1",
                "bravio_id": "99824",
                "revision": "A",
                "sequence_int": base_seq + 3,
                "color_temp_bin": "5000K",  # 差异档位
                "flux_bin": "1000LM",
                "voltage_bin": "12V"
            },
            headers=headers
        )
        sn3 = sn3_diff_res.json()["serial_number"]
        mismatch_res = await client.post(
            "/api/v1/traceability/pairing/check-box",
            json={
                "box_barcode": f"BOX-99824-2642-{base_seq+1:06d}",
                "sn_first": sn1,
                "sn_second": sn3
            },
            headers=headers
        )
        assert mismatch_res.status_code == 200
        assert mismatch_res.json()["is_pass"] is False
        assert mismatch_res.json()["status"] == "MISMATCH"

@pytest.mark.asyncio
async def test_wms_packaging_tree_and_rma_fraud_detection():
    """测试四级包装聚合、德国仓抽检拆箱与售后换盒欺诈拦截 (docs/08 & docs/09)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 聚合装箱 (CARTON -> 多个 BOX)
        pack_res = await client.post(
            "/api/v1/wms/pack",
            json={
                "parent_code": "CTN-99824-2642-0010",
                "parent_level": "CARTON",
                "child_codes": ["BOX-99824-2642-000501", "BOX-99824-2642-000502"],
                "bravio_id": "99824",
                "warehouse_location": "MUC-WH-A-01"
            },
            headers=headers
        )
        assert pack_res.status_code == 200
        assert pack_res.json()["success"] is True

        # 2. 德国仓抽检解包
        dec_res = await client.post(
            "/api/v1/wms/deconstruct-sample",
            json={
                "carton_code": "CTN-99824-2642-0010",
                "box_code_to_remove": "BOX-99824-2642-000501",
                "reason": "德国仓入库 IQC 抽检留样"
            },
            headers=headers
        )
        assert dec_res.status_code == 200
        assert dec_res.json()["carton_status"] == "PARTIAL_OPENED"

        # 3. 售后 RMA 申请：拿错误的彩盒码退货，触发换盒欺诈拦截
        # 先获取前面绑定的 sn1
        sn1_code = "99824A2642000005016000K1200LM12V"
        rma_fraud_res = await client.post(
            "/api/v1/rma",
            json={
                "customer_name": "欺诈测试客户",
                "returned_sn": sn1_code,
                "returned_box_code": "BOX-FAKE-WRONG-BOX", # 错误的彩盒
                "claim_reason": "车灯不亮要求换新"
            },
            headers=headers
        )
        assert rma_fraud_res.status_code == 201
        rma_data = rma_fraud_res.json()
        assert rma_data["is_fraud_detected"] is True
        assert rma_data["status"] == "FRAUD_REJECTED"
        assert "换盒欺诈拦截" in rma_data["fraud_reason"]

@pytest.mark.asyncio
async def test_qms_ecm_dms_b2b_and_backup():
    """测试 QMS 质检、8D攻关、ECM 工程变更、DMS 受控知识库、B2B 外协与数据库快照 (docs/13, 14, 15, 16, 05)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. 录入出厂 FQC 质检单
        qc_res = await client.post(
            "/api/v1/qms/inspections",
            json={
                "inspection_type": "FQC",
                "product_id": "prod_1",
                "bravio_id": "99824",
                "batch_number": "BATCH-2026-10",
                "sample_size": 10,
                "defect_count": 0,
                "dimension_check_passed": True,
                "optical_check_passed": True,
                "kba_cop_compliant": True,
                "overall_result": "PASS"
            },
            headers=headers
        )
        assert qc_res.status_code == 201
        assert qc_res.json()["overall_result"] == "PASS"

        # 2. 发起 8D 异常攻关工单
        eight_d_res = await client.post(
            "/api/v1/qms/incidents-8d",
            json={
                "title": "透镜封装边缘微小气泡异常",
                "product_id": "prod_1",
                "source": "FQC_INSPECTION",
                "d1_team_leader": "刘质保 (QE)",
                "d2_problem_description": "抽检发现 1 支透镜边缘存在 0.1mm 气泡"
            },
            headers=headers
        )
        assert eight_d_res.status_code == 201
        incident_id = eight_d_res.json()["id"]

        # 推进 8D 措施
        up_8d = await client.put(
            f"/api/v1/qms/incidents-8d/{incident_id}",
            json={
                "status": "CAPA_ACTIONS",
                "d3_interim_containment": "全检本批次库存，隔离可疑物料",
                "d4_root_cause": "注塑模具温控器传感器漂移 3 摄氏度导致填充不均"
            },
            headers=headers
        )
        assert up_8d.status_code == 200
        assert up_8d.json()["status"] == "CAPA_ACTIONS"

        # 3. 发起工程变更 ECO
        eco_res = await client.post(
            "/api/v1/ecm",
            json={
                "product_id": "prod_1",
                "title": "注塑模具温控补偿与图纸公差升级",
                "change_type": "PROCESS",
                "reason": "8D 攻关对策落实与防呆升级",
                "affects_drawings": True,
                "affects_bom": False,
                "affects_kba_homologation": True,
                "kba_eval_notes": "经评估不改变光型照射角度，生产一致性 CoP 保持受控"
            },
            headers=headers
        )
        assert eco_res.status_code == 201
        eco_id = eco_res.json()["id"]

        # 批准 ECO
        appr_eco = await client.post(
            f"/api/v1/ecm/{eco_id}/review",
            json={"approved": True, "notes": "工程总监与质量总监会签通过"},
            headers=headers
        )
        assert appr_eco.status_code == 200
        assert appr_eco.json()["status"] == "APPROVED"

        # 4. 查询受控文档 DMS (包含预设质量手册)
        dms_res = await client.get("/api/v1/dms/documents", headers=headers)
        assert dms_res.status_code == 200
        docs = dms_res.json()
        assert len(docs) >= 2
        assert any(d["doc_number"] == "QM-001" for d in docs)

        # 5. 下达 B2B 代工工单并预分配条码
        partner_res = await client.get("/api/v1/partners", headers=headers)
        assert partner_res.status_code == 200
        sup_id = partner_res.json()[0]["id"]
        wo_res = await client.post(
            "/api/v1/b2b/work-orders",
            json={
                "partner_id": sup_id,
                "product_id": "prod_1",
                "bravio_id": "99824",
                "planned_quantity": 200
            },
            headers=headers
        )
        assert wo_res.status_code == 201
        wo_data = wo_res.json()
        assert wo_data["planned_quantity"] == 200
        assert "99824" in wo_data["sn_range_start"]

        # 6. 数据库一致性备份与防篡改 SHA256 校验
        snap_res = await client.post(
            "/api/v1/system/backups/snapshot",
            json={"notes": "V0.3 构建验证安全一致性快照"},
            headers=headers
        )
        assert snap_res.status_code == 201
        b_data = snap_res.json()
        assert len(b_data["sha256_checksum"]) == 64

        verify_res = await client.get(f"/api/v1/system/backups/{b_data['id']}/verify", headers=headers)
        assert verify_res.status_code == 200
        assert verify_res.json()["is_tamper_free"] is True
