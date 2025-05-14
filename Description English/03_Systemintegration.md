# System Integration
https://www.creditreform.ch/loesungen/systemintegration

CrediCONNECT connection to ERP / accounting for credit checks | RiskCUBE connection to online shop for approval of purchase on account | Collection solution for optimized receivables management

## CrediCONNECT
https://www.creditreform.ch/loesungen/systemintegration/individuelle-anbindung
- The Swiss business database can be connected directly to core applications such as ERP or CRM systems.
- Credit checks, monitoring of credit limits, and other processes can be automated and integrated into business processes.
- **Flexible connection options**: Creditreform enables access via various common protocols and connections.
- **Adaptation to customer systems**: Integration into different infrastructures is possible, from simple to complex.
- **Technical and professional consulting**: Comprehensive support for the individual implementation of your needs.

### CrediCONNECT – Maximum Integration:
- **Realtime interface** for fast and flexible data integration.
- Supports systems such as:
  - CRM systems
  - ERP systems
  - Scorecards
  - Own web applications
- **XML format** for structured, electronic data exchange.
- **Individually scalable degree of automation**: From fully automated POS systems to manually controlled applications.
- Also available as a **WebService**.

### Individual connections possible for:
- Address management
- Commercial register data
- Credit and business information
- Economic interconnections
- Monitoring

### Ready4 Credit Management – Switzerland for SAP
https://www.creditreform.ch/fileadmin/user_upload/central_files/_documents/01_loesungen/14_systemintegration/_erp_cmgmt/00_ProduktFlyer_Ready4CMGMT_CH_DE_202308.pdf

#### Scope of Services
"Ready4 Credit Management – Switzerland" is a credit management system. Individual subprocesses such as customer identification and risk assessment during credit granting can be handled efficiently and transparently in SAP.

#### Customer Benefits
- **Time savings:** No system break due to seamless integration.
- **Process simplification:** For master data creation, risk assessment, and monitoring.
- **Fast and cost-effective implementation project.**
- **Storage of all information** in SAP® in a structured form; avoids multiple queries.
- **Efficient analysis** of risk structure and credit-relevant characteristics.
- **Fully automated linking of master data** (debtors, creditors, or business partners) with Creditreform information. If necessary, easy cleansing of master data via standard functions.
- **Integration** into the Creditreform payment pool Xchange.

#### Architecture
- AddOn runs on the same SAP-ERP system under its own SAP partner namespace.
- No collision with in-house developments.
- Encrypted communication based on web standards.

#### Provider of the SAP AddOn
The SAP AddOn is distributed by **SOA People AG**. This SAP Gold Partner is a leading provider of SAP-integrated credit management standard solutions. Hundreds of customers rely on their services.

**SOA People AG**  
Fautenbruchstrasse 46  
D-76137 Karlsruhe  
[www.soapeople.com](http://www.soapeople.com)

#### Functions
- Online search and retrieval of companies (Switzerland and Liechtenstein) as well as private individuals (Switzerland).
- Online search and retrieval of foreign information.
- Batch retrieval and batch processing (mass retrieval).
- Ordering and management of research and monitoring orders.
- Ordering of debt collection information with upload of proof of interest, structured display of information as PDF.
- Extraction of Xchange payment experience.

#### SAP Integration
- Integration into SAP credit management FD32 / FD33.
- Integration into SAP business partner and FSCM.
- Classic user interface in SAPGUI.
- Redesigned user interface in Fiori.

#### Procedure
**1. Kick-off meeting**  
Creditreform specialists record the business needs on site. Results and solution proposals are documented, total costs roughly estimated.

**2. Live presentation**  
Creditreform organizes a web conference to demonstrate functions live and clarify technical questions.

**3. Contract signing and project planning**  
After contract conclusion, planning of installation and user training follows.

#### Prices (excl. VAT)
- **Rental price incl. software maintenance (READY4 Credit Rating Bureaus)**  
  One company code on a productive client:  
  **Euro 6,000 per year**  
  *(additional company codes on request)*

- **Commissioning, customizing, and training**  
  **Euro 1,360 per day** *(experience shows: approx. 3-4 days)*

- **Available languages:** German, French (other languages on request)

**Note:**  
For members with an existing module, there are no license costs when switching to the new AddOn. For data transfer and commissioning, a flat rate of **Euro 5,000** applies.

#### Requirements
- Membership with Creditreform
- SAP® ECC 6.0 from EhP5 or S/4HANA

## RiskCUBE

**RiskCUBE** is a solution from Creditreform that offers the payment method "purchase on account" in online shops only to credit-checked customers with a calculable risk. Through an intelligent set of rules, risks and fraud attempts are detected and minimized. Shop operators can thus safely integrate the "invoice" payment method, which, according to experience, leads to a higher conversion rate and increased sales.

> *"With this module, we can now also sell on account in the webshop. Since then, our sales have increased by 30%." – Markus Roger Jenny, Managing Director, deinKonzept GmbH, Uznach*

### Need

- "Invoice" is the most popular payment method in Swiss online retail.
- If this payment method is not offered, there is an increased risk of purchase abandonment.
- Without a credit check, there is a potentially high risk of payment defaults.
- RiskCUBE is intended to ensure that only customers with sufficient creditworthiness can use the purchase on account option.

### Background

- Due to the high popularity of purchase on account, fraud and payment defaults are a problem.
- RiskCUBE determines, based on a credit check and other factors, whether the invoice option can be offered.

### Scope of Services

1. **Credit check before displaying payment options**  
   - After entering address details in the order process, the data is passed to RiskCUBE.
   - RiskCUBE determines the creditworthiness and behavior of the buyer.
   - Depending on the result, payment methods are restricted or allowed.

2. **Individual configuration options**  
   - Invoice option only with sufficient creditworthiness.
   - On request: no invoice option in case of suspicious behavior, invalid address, or exceeding credit limits.
   - Option to still allow the "invoice" payment method for medium creditworthiness (yellow) or unknown person (no match).

3. **Risk control**  
   - Approval or blocking rules for certain time windows (e.g., night block between 01:00 and 04:30).
   - Definable minimum order values, maximum credit limits, and match tolerances.

### Fraud Detection

- **Suspicious behavior in the shop**: If there are fraud indicators (e.g., multiple orders in a short time, differing delivery address, etc.), the "invoice" payment method can be deactivated.
- **Postal invalid addresses**: No invoice option if the address does not exist or has already been reported as suspicious.
- **Time-based restrictions**: Night block (no purchase on account between 01:00 and 04:30).
- **Known fraud addresses**: Blocked and reported by Creditreform.
- **Supplementary IP fraud analysis**: Recommendation to use additional fraud add-ons.

### Control Options (Excerpt)

- **Match tolerance**: Adjustable to allow, for example, minor spelling errors in addresses.
- **Minimum order value per transaction**: Purchase on account only from a certain purchase value.
- **Individual credit limits**:  
  - B2B/B2C, per day and/or within a defined period (e.g., 30 days).
  - Different limits depending on credit traffic light (green/yellow/red) or special customer type (public administration, etc.).
- **Maximum credit limit in case of system failure**: Fallback rule if RiskCUBE or the interface is not available.
- **Different billing and delivery address**: Allow or block as desired.
- **Payment disruptions**: Automatic exclusion from purchase on account in case of past payment disruptions.

### Procedure (General)

1. **Submit information to Creditreform**  
   - Shop software and version
   - Expected number of shop orders per year
   - Planned date for installation (plug-in or interface)

2. **Check by Creditreform**  
   - Joint clarification with the respective development partner whether a plug-in exists for your shop version or an individual connection is necessary.
   - Preparation of an offer for credit checks.

3. **Contract conclusion and installation**  
   - After contract conclusion, a Creditreform project manager coordinates the installation or connection.
   - You receive access data, technical documentation, and further details for configuring your risk control.

### Available Shop Plug-ins & Systems

#### General Overview

- **Magento** (from version 2.2)
- **PrestaShop** (version 8.1.x)
- **Gambio** (from version 3.14)
- **WooCommerce** (WordPress from version 5.3, PHP from version 7.4)
- **Shopware** (from version 6 with RiskCUBE, from version 5.1.0 without RiskCUBE)
- **PepperShop** (from version 9 with RiskCUBE, up to version 8 without RiskCUBE)
- **AbaShop** (from version 2016 without RiskCUBE, with separate credit check)

A current overview of all plug-ins:  
[plugin.creditreform.ch](http://plugin.creditreform.ch)

#### Magento & Shopware

- **Supported countries**: Switzerland, Liechtenstein (for companies)
- **Prices**
  - Use and setup of the RiskCUBE license: CHF 960 per year
  - Setup costs (one-time): €399 (incl. 2 hours support)
  - Module costs: €39 per month (annual prepayment)
  - Credit check: Individual offer by Creditreform (flat rates cheaper with additional collection or provision of payment experiences)

- **Plug-in partner**
  - *LEONEX Internet GmbH*
    Technologiepark 6, DE-33100 Paderborn
    +49 5251 4142 500
    [www.leonex.de](https://www.leonex.de)
    info@leonex.de

#### PrestaShop & WooCommerce

- **Supported countries**: Switzerland, Liechtenstein
- **Prices**
  - Use and setup of the RiskCUBE license incl. shop plug-in: CHF 960 per year
  - Credit check: Individual offer (flat rates possible, cheaper with additional collection or provision of payment experiences)

- **Download**
  - **WooCommerce**: [WordPress plug-in](https://wordpress.org/plugins/riskcube-von-creditreform-schweiz)
  - **PrestaShop**: [addons.prestashop.com](https://addons.prestashop.com/de/search.php?search_query=riskcube&compatibility=8.1.7&)

- **Plug-in partner**
  - *Masterhomepage GmbH*
    Thiersteinerallee 17, 4053 Basel
    +41 61 681 54 50
    [masterhomepage.ch](https://www.masterhomepage.ch)
    info@masterhomepage.ch

#### PepperShop

- **Supported countries**: Switzerland, Liechtenstein (for companies)
- **Prices**
  - RiskCUBE license with plug-in: CHF 960 p.a.
  - RiskCUBE license *without* plug-in: CHF 660 p.a.
  - Shop plug-in usage fee: CHF 9.60 per month (minimum term 12 months)
  - Credit check: Individual offer (flat rates cheaper with additional collection or provision of payment experiences)

- **Plug-in partner**
  - *Glarotech GmbH*
    Toggenburgerstr. 156, 9500 Wil
    [www.peppershop.com](https://www.peppershop.com)

#### Gambio

- **Supported countries**: Switzerland, Liechtenstein (for companies)
- **Prices**
  - Use and setup of the RiskCUBE license incl. shop plug-in: CHF 960 p.a.
  - Shop plug-in:
    - License per URL (one-time): €150 (maintenance/upgrade as needed)
    - License per URL *incl. maintenance/upgrade*: €29 per month (minimum term 12 months)
    - Installation support (one-time, recommended): €340
  - Credit check: Individual offer (flat rates cheaper with additional collection or payment experiences)

- **Plug-in partner**
  - *WinHelp GmbH*
    Bienwaldstrasse 41, DE-76287 Rheinstetten
    +49 721 8198 7100
    [www.winhelp.eu](https://www.winhelp.eu)
    info@winhelp.eu

#### AbaShop with integrated credit check

- **Supported countries**: Switzerland, Liechtenstein (for companies)
- **Prices**
  - Operation of the module: CHF 20.00 per month
  - Credit check: Separate offer by Creditreform
  - Costs for the AbaShop option "credit check": Billed by the respective Abacus sales partner

> *"With the additional option for AbaShop, the credit check is automatically integrated into the shop. This saves time and provides security."
– Bruno Rhomberg, Member of the Executive Board, Creditreform Egeli Group*

- **Risk setting with traffic light control**
  - Depending on the score of the credit check, a traffic light (green/yellow/red) is provided.
  - Settings for different risk appetites (low, medium, high).
  - Optional: Check only for companies or only for new customers.

- **Configuration options for payment methods** (examples from AbaShop):
  - Credit check before, during, or after payment selection.
  - Time interval for updating the credit check.
  - Invoice option for credit yellow (yes/no), no match (yes/no), or in case of connection error (yes/no).
  - Restriction to shopping carts from CHF X to CHF Y.
  - Minimum order amounts for displaying the invoice option.

**Requirements**
- Abacus from version 2016
- Membership with Creditreform
- If applicable, collection processing via Creditreform (recommended)

### RiskCUBE API & Individual Connection

- **REST interface**
  - Modern, scalable REST API for individual solutions.
  - Documentation and access data are provided after signing a confidentiality agreement.

- **Without RiskCUBE**
  - Even without RiskCUBE functions, you can integrate (modified) credit checks for your shop.
  - Requires separate interface documentation and possibly own development.

### Prices (Summary)

1. **RiskCUBE license**
   - **With shop plug-in**: CHF 960 p.a. (unless otherwise stated)
   - **Without shop plug-in**: CHF 660 p.a.
   - Different prices depending on the system (see respective details above).

2. **Shop plug-in costs**
   - Partly monthly, partly one-time license or installation costs depending on system and partner.

3. **Credit check**
   - Individual offers with flat rates (discounted with additional collection or provision of payment experiences).

4. **Other costs**
   - Installation, maintenance, upgrade, or support according to the information provided by the respective plug-in partners.

*All prices are exclusive of value-added tax (VAT).*

### Contact Creditreform AG

- **Address**
  Teufener Strasse 36
  CH-9000 St. Gallen
- **Phone**
  +41 71 221 11 99
- **E-mail**
  support@creditreform.ch

For detailed information on plug-ins, prices, credit checks, and collections, please contact your account manager or visit  
[plugin.creditreform.ch](http://plugin.creditreform.ch).

## Collection Solution
https://www.creditreform.ch/loesungen/systemintegration/forderungsmanagement-und-zahlungsabwicklung
- **Optimized receivables management**
  - Manage receivables efficiently without giving up control
  - Reduce costs and effort (accounts receivable management, outstanding payments, debt collection)
  - Solutions from EGELI Informatik sustainably simplify processes in collections

- **Integrated interfaces to Creditreform for:**
  - Debtor identification
  - Credit assessment
  - Debtor monitoring (name and address changes, credit changes, bankruptcy notifications)
  - Obtaining official information (residents' registration, debt collection information)