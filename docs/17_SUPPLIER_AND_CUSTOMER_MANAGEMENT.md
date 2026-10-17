# 17 - 供应商与客户管理模块规范 (Supplier & Customer Management - Odoo Style)

---

## 1. 业务目标与 Odoo 交互设计哲学

用户的核心原则：  
> **“根据以上创建两个模块：供应商管理模块，客户管理模块。暂时不要太复杂，包含基本信息即可，参考 Odoo。”**

在 Odoo 的原生体验中，商业伙伴（`res.partner`）采用统一、干净、可自由切换“客户 / 供应商”身份的经典设计模式。  
Bravio ERP 遵循此哲学，在保证底层现代关系型数据库规范化的同时，提供极简高效的卡片看板（Kanban）、多地址切换及右上角智能统计按钮（Smart Buttons）。

---

## 2. 供应商管理模块规范 (Supplier Management)

供应商是 Bravio 生产订单下发、32 位条码打标、BOM 图纸受控传输以及出厂终检（FQC）数据回传的对端组织。

### 2.1 基础信息与业务属性
- **编码与名称**：代工厂唯一代码（`partner_id`，如: `SUPP_0013`）、全称、商业注册号、纳税人识别号（VAT / Tax ID）。
- **供应商类型**：`SMT_ELECTRONICS` (PCBA贴片)、`DIE_CASTING` (压铸与散热壳体)、`FINAL_ASSEMBLY` (总成制造代工厂)、`PACKAGING` (包材包装厂)。
- **质量资质评级 (Quality Tier)**：
  - 是否持有有效 ISO 9001 认证证书及发证机构。
  - 是否通过德国 KBA 生产一致性（CoP）现场初审。
  - 供应商质量评级：`TIER_A` (免检直通)、`TIER_B` (正常加严抽检)、`TIER_C` (重点整改监控)。
- **结算与采购条款**：结算币种（EUR, USD, CNY）、账期方式（如：TT 30天、出货见提单付款）。

### 2.2 Odoo 风格供应商表单布局 (Supplier Form View)
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ [新建] [保存]   Bravio ERP  /  供应商管理  /  富强电子科技 (东莞) 有限公司      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [工厂厂徽]  富强电子科技 (东莞) 有限公司        [ 🪪 8 张采购工单 ] [ 📈 PPM: 120 ]│
│            代码: SUPP-0013   类型: 总成代工     [ 🔐 API 密钥: 启用 ] [ ⭐ A级 ]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [基本联系信息]   [送货与工厂地址]   [质量与KBA认证]   [采购与结算条款]   [API对接凭证] │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 办公地址: 广东省东莞市大朗镇科技产业园 8 栋                                     │
│ 主联系人: 陈总监 (生产运营)     电话: +86 138-0000-0000   邮箱: ops@fuqiang.com │
│ 商务接口: 林经理 (商务报价)     电话: +86 139-0000-0000   邮箱: sales@fuqiang.com│
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 客户管理模块规范 (Customer Management)

客户涵盖欧洲及全球的整车厂（OEM）、一级车灯改装总成商、区域核心分销商（B2B Distributor）及大型售后连锁零售体系。

### 3.1 基础信息与核心字段
- **客户基本档案**：客户代码（`partner_id`，如: `CUST_DE_001`）、公司法定注册名称、所在国家（如: `DE`, `PL`, `FR`）。
- **客户层级分类**：
  - `B2B_DISTRIBUTOR`（欧洲区域总分销商，整盘整托进出）。
  - `OEM_AUTOMAKER`（主机厂配套/特种车辆改装客户）。
  - `RETAIL_CHAIN`（大型汽车配件连锁门店/电商自营仓）。
- **多送货网点管理 (Multi-Address Logistics)**：
  - 支持一个客户关联多个物理收货仓库（例如某德国大分销商在慕尼黑、汉堡、华沙拥有独立卸货库位）。
  - 仓库物流 API 可在临发货前指定特定的收货网点代码。
- **质保与风控条款**：
  - 约定 B2B 质保月数（`warranty_months_b2b`，默认 18 或 24 个月，直接关联 RMA 逆向风控计算）。
  - 信用额度与账期控制。

### 3.2 Odoo 风格客户表单布局 (Customer Form View)
- **右上角智能按钮 (Smart Buttons)**：
  - `[ 🛒 12 张销售订单 ]`（快速查看采购流水）。
  - `[ 🚚 45 批物流发运 ]`（实时查看在途与已交付托盘）。
  - `[ 🛡️ 2 项 RMA 客诉 ]`（点击直接穿透到 RMA 逆向风控与 8D 报告）。
  - `[ 💶 待结算应收账款 ]`。

---

## 4. 数据库模型统一设计 (`partners`, `partner_addresses`, `partner_contacts`)

将供应商与客户统一抽象至轻量优雅的高性能数据模型：

```sql
CREATE TYPE partner_type_enum AS ENUM ('SUPPLIER', 'DISTRIBUTOR', 'OEM_TIER1', 'RETAILER', 'LOGISTICS_3PL');

-- 核心商业伙伴表 (统一支撑供应商与客户)
CREATE TABLE partners (
    partner_id VARCHAR(32) PRIMARY KEY,         -- 客户/供应商自定义唯一代码 (如: SUPP-0013, CUST-DE-001)
    partner_name VARCHAR(150) NOT NULL,         -- 机构法定商业全称
    partner_type partner_type_enum NOT NULL,    -- 核心类型分类
    is_supplier BOOLEAN DEFAULT FALSE,          -- 是否具备供应商身份
    is_customer BOOLEAN DEFAULT FALSE,          -- 是否具备客户身份
    
    -- 注册地与税务信息
    country_code CHAR(2) DEFAULT 'DE',          -- ISO 国家二字码
    tax_identifier VARCHAR(50),                 -- 欧盟增值税号 (VAT Number) 或统一税号
    commercial_registry_no VARCHAR(50),         -- 工商注册登记号 (HRB / Unified Code)
    
    -- 商务与结算条款
    currency CHAR(3) DEFAULT 'EUR',             -- 结算本位币: EUR, USD, CNY
    payment_terms VARCHAR(50) DEFAULT 'NET_30', -- 账期: 'ADVANCE', 'NET_30', 'NET_60'
    credit_limit NUMERIC(12, 2) DEFAULT 0.00,   -- 授信额度
    warranty_months_b2b INT DEFAULT 24,         -- 质保服务期 (用于 RMA 判定)
    
    -- 质量体系与认证 (针对供应商关键)
    quality_tier VARCHAR(20) DEFAULT 'TIER_B',  -- 'TIER_A', 'TIER_B', 'TIER_C'
    is_iso9001_certified BOOLEAN DEFAULT TRUE,
    is_kba_cop_audited BOOLEAN DEFAULT FALSE,
    
    -- 状态与风控冻结锁 (Hold Flags)
    is_active BOOLEAN DEFAULT TRUE,
    is_quality_hold BOOLEAN DEFAULT FALSE,      -- 质量冻结: 阻断工单生产、阻断条码预分配与入库
    quality_hold_reason TEXT,
    is_financial_hold BOOLEAN DEFAULT FALSE,    -- 财务冻结: 超期欠款阻断销售出运与审批
    financial_hold_reason TEXT,
    
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by_id UUID,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by_id UUID,
    is_deleted BOOLEAN DEFAULT FALSE,
    version_id INT DEFAULT 1
);

-- 多送货地址/物理网点管理表 (一对多)
CREATE TABLE partner_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id VARCHAR(32) NOT NULL REFERENCES partners(partner_id) ON DELETE CASCADE,
    address_type VARCHAR(20) DEFAULT 'DELIVERY', -- 'INVOICE' (开票地址), 'DELIVERY' (送货卸货口), 'FACTORY' (工厂厂址)
    address_name VARCHAR(100) NOT NULL,         -- 网点简称，如: "慕尼黑 2 号中央分拨中心"
    recipient_name VARCHAR(100),                -- 现场收货联系人
    recipient_phone VARCHAR(50),                -- 联系电话
    street_line1 TEXT NOT NULL,                 -- 街道门牌
    street_line2 TEXT,                          -- 楼宇/卸货泊位号
    postal_code VARCHAR(20) NOT NULL,           -- 邮编
    city VARCHAR(50) NOT NULL,                  -- 城市
    country_code CHAR(2) DEFAULT 'DE',
    is_default BOOLEAN DEFAULT FALSE
);

-- 伙伴关键联系人矩阵表
CREATE TABLE partner_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id VARCHAR(32) NOT NULL REFERENCES partners(partner_id) ON DELETE CASCADE,
    contact_name VARCHAR(100) NOT NULL,         -- 姓名
    department_role VARCHAR(50),                -- 职能: 'QUALITY', 'LOGISTICS', 'SALES', 'FINANCE'
    email VARCHAR(100),
    mobile_phone VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_partners_type ON partners(partner_type);
CREATE INDEX idx_partners_country ON partners(country_code);
CREATE INDEX idx_partner_addresses_partner ON partner_addresses(partner_id);
```
