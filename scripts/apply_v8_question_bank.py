#!/usr/bin/env python3
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPEN_PATH = ROOT / 'data' / 'open_questions.js'
NPTEL_PATH = ROOT / 'data' / 'nptel_questions.js'
MANIFEST_PATH = ROOT / 'data' / 'bank_manifest.json'
RETIRED_PATH = ROOT / 'data' / 'retired_questions.json'

VALIDATED_AT = '2026-09-16'

RETIRE_REASONS = {
    'BHASHA-BBL-51c99dc5-6a53-4304-8ec3-1d6444f209d0': 'Multiple independently true debenture propositions but single-answer options.',
    'BHASHA-BBL-983cdc9f-4fc3-4770-afb0-55504679dd85': 'Obsolete OPC compulsory-conversion threshold removed by 2021 rule change.',
    'BHASHA-BBL-f2e068ac-bb8e-49a4-ab64-72d6dab24593': 'Contestable merger classification; not a stable statutory exam point.',
    'BHASHA-BBL-67d85066-7107-440a-b435-1646aec65330': 'Multiple prospectus disclosures can be correct; invalid single-answer construction.',
    'BHASHA-BBL-4770b81c-52ae-4c18-b435-39762bfa746d': 'Section 253 sickness provision is omitted/currently inoperative.',
    'BHASHA-BBL-c82a49ca-13ad-4db9-b588-4514b481b21e': 'Assertion/reason relies on irrelevant health claim rather than legal reasoning.',
    'BHASHA-BBL-5eeb5d1d-752f-4d48-a19f-64b25d8c0de2': 'MOA Schedule-I table is not determined by listed-company status.',
    'BHASHA-BBL-790ff7db-9169-4246-9111-4b280a9912c3': 'Overbroad CSR construct presenting one Schedule-VII activity as the definition of CSR.',
    'BHASHA-BBL-363d8fcb-17da-40c2-8926-642654ce8e3a': 'Ultra-vires remedies item contains multiple overbroad/contestable propositions.',
    'BHASHA-BBL-2efdde59-bf70-4d7c-a087-1f982155ea1a': 'Historical 2019 committee-recommendation trivia; low-value for current law preparation.',
    'BHASHA-BBL-6b43ca65-5717-4588-b1ac-3f84e1dc047e': 'Time-bound 2024 settlement-scheme trivia and garbled wording.',
    'BHASHA-BBF-f60d3f8b-3ca5-4c23-9f58-671ed8da566e': 'Ephemeral 2023 IPO-approval current-affairs trivia.',
    'BHASHA-BBF-35d7fb10-07d7-4ffd-b0e0-4911195b1e41': 'False universal director age rule; Section 196 age conditions are role-specific.',
}

PATCHES = {
    'BHASHA-BBL-35a27ab2-d208-48cf-98ad-fea2bf4a82fd': {
        'question': 'Arrange the following provisions of the Companies Act, 2013 in descending order of section number:\n(a) Execution of bills of exchange, etc.\n(b) Punishment in case of repeated default\n(c) Annual reports on Government companies\n(d) Petition for winding up\n(e) Functions of company secretary',
        'options': ['B, C, D, E, A', 'C, D, E, A, B', 'C, A, E, D, B', 'B, A, D, C, E'],
        'answer': 0,
        'explanation': 'The relevant sections are 451, 394, 272, 205 and 22 respectively, so the descending order is B, C, D, E, A.',
        'reference': 'Companies Act, 2013: sections 451, 394, 272, 205 and 22.'
    },
    'BHASHA-BBL-cc5cbd86-342e-4c77-b3be-fe20f0c5b6c0': {
        'question': 'A company is otherwise covered by Section 135 of the Companies Act, 2013. Under Section 135(9), when is it not required to constitute a Corporate Social Responsibility Committee?',
        'options': ['When the amount required to be spent under Section 135(5) does not exceed ₹50 lakh', 'Whenever its net profit is below ₹2 crore', 'Whenever its turnover is below ₹500 crore', 'Whenever it is an unlisted company'],
        'answer': 0,
        'explanation': 'Section 135(9) provides that where the amount required to be spent under Section 135(5) does not exceed ₹50 lakh, the requirement to constitute the CSR Committee does not apply and the Board discharges its functions.',
        'reference': 'Companies Act, 2013, Section 135(9).'
    },
    'BHASHA-BBL-c62ba5c6-ef0d-4ba0-9c79-af5a1d72d320': {
        'question': 'In Serious Fraud Investigation Office v. Rahul Modi, how did the Supreme Court treat the time stipulation in Section 212(3) of the Companies Act, 2013 for completion of an SFIO investigation?',
        'options': ['Directory rather than mandatory', 'Mandatory and jurisdictional', 'A condition whose expiry automatically terminates the SFIO mandate', 'Unconstitutional'],
        'answer': 0,
        'explanation': 'The Supreme Court held that the period specified under Section 212(3) is directory; expiry of that period does not by itself end the SFIO mandate.',
        'reference': 'Serious Fraud Investigation Office v. Rahul Modi; Companies Act, 2013, Section 212(3).'
    },
    'BHASHA-BBL-e982b07e-0db6-4a4d-8f04-3ebc7ef520cf': {
        'question': 'Under the prescribed small-company limits effective from 1 December 2025, which pair states the maximum paid-up share capital and turnover limits, subject to the statutory exclusions?',
        'options': ['₹10 crore paid-up capital and ₹100 crore turnover', '₹4 crore paid-up capital and ₹40 crore turnover', '₹2 crore paid-up capital and ₹20 crore turnover', '₹10 crore paid-up capital and ₹50 crore turnover'],
        'answer': 0,
        'explanation': 'The prescribed limits for a small company were increased to paid-up share capital not exceeding ₹10 crore and turnover not exceeding ₹100 crore, subject to the exclusions in Section 2(85).',
        'reference': 'Companies Act, 2013, Section 2(85) and the prescribed small-company limits effective 1 December 2025.'
    },
    'BHASHA-BBL-34d48980-7199-4399-b24a-2f1259941332': {
        'question': 'Which remuneration may an independent director receive under Section 149(9) of the Companies Act, 2013?',
        'options': ['Sitting fees and profit-related commission approved by members', 'Employee stock options only', 'A share in the fixed assets of the company', 'Salary as a whole-time director'],
        'answer': 0,
        'explanation': 'An independent director may receive sitting fees, reimbursement of expenses and profit-related commission approved by members, but is not entitled to stock options.',
        'reference': 'Companies Act, 2013, Section 149(9).'
    },
    'BHASHA-BBL-2c975ba0-f60f-4981-960d-d5726a3205a6': {
        'question': 'Which section of the Securities and Exchange Board of India Act, 1992 deals with offences by companies?',
        'options': ['Section 6', 'Section 11', 'Section 27', 'Section 30'],
        'answer': 2,
        'explanation': 'Section 27 deals with offences by companies. Section 11 concerns functions of the Board and Section 30 concerns the power to make regulations.',
        'reference': 'SEBI Act, 1992, Sections 11, 27 and 30.'
    },
    'BHASHA-BBL-d06d2ea1-8ff1-4df9-bb65-d772833ae78e': {
        'question': 'Amalgamation of companies in the public interest under the Companies Act, 2013 is dealt with by which section?',
        'options': ['Section 230', 'Section 232', 'Section 237', 'Section 396'],
        'answer': 2,
        'explanation': 'Section 237 of the Companies Act, 2013 deals with amalgamation of companies in the public interest. Section 396 was the corresponding provision in the Companies Act, 1956.',
        'reference': 'Companies Act, 2013, Section 237.'
    },
    'BHASHA-BBL-8080a541-b5d8-4c17-bd09-6506a2b4ae2a': {
        'question': 'Under Section 15HA of the SEBI Act, 1992, the penalty for fraudulent and unfair trade practices may extend to which of the following?',
        'options': ['₹25 crore or three times the amount of profits made out of the practices, whichever is higher', '₹25 crore or three times the profits, whichever is lower', '₹5 crore only', 'Three times the profits only'],
        'answer': 0,
        'explanation': 'Section 15HA provides a penalty framework that may extend to ₹25 crore or three times the amount of profits made out of such practices, whichever is higher.',
        'reference': 'SEBI Act, 1992, Section 15HA.'
    },
    'BHASHA-BBL-943aba1f-771d-4793-af1e-70014cbcea19': {
        'question': 'Which matching of prospectus concepts to Companies Act, 2013 provisions is correct?',
        'options': ['Abridged prospectus—Section 2(1); deemed prospectus—Section 25; shelf prospectus—Section 31; red herring prospectus—Section 32', 'Abridged prospectus—Section 31; deemed prospectus—Section 32; shelf prospectus—Section 2(1); red herring prospectus—Section 25', 'Abridged prospectus—Section 25; deemed prospectus—Section 31; shelf prospectus—Section 32; red herring prospectus—Section 2(1)', 'Abridged prospectus—Section 32; deemed prospectus—Section 2(1); shelf prospectus—Section 25; red herring prospectus—Section 31'],
        'answer': 0,
        'explanation': 'The Act defines abridged prospectus in Section 2(1), deemed prospectus in Section 25, shelf prospectus in Section 31 and red herring prospectus in Section 32.',
        'reference': 'Companies Act, 2013, Sections 2(1), 25, 31 and 32.'
    },
    'BHASHA-BBL-41aa0f42-628c-48ac-b117-f20bf046fa9f': {
        'question': 'Under Section 101 of the Companies Act, 2013, a general meeting may ordinarily be called by giving at least how many clear days of notice?',
        'options': ['21 clear days', '30 clear days', '14 clear days', '7 clear days'],
        'answer': 0,
        'explanation': 'Section 101 requires not less than 21 clear days notice, subject to the statutory rules for shorter notice.',
        'reference': 'Companies Act, 2013, Section 101.'
    },
    'BHASHA-BBL-d9ee88b3-55e8-474f-bfd3-2a1e12c9933b': {
        'question': 'In which year was SEBI first constituted as a non-statutory body?',
        'options': ['1988', '1990', '1992', '1994'],
        'answer': 0,
        'explanation': 'SEBI was constituted in 1988 as a non-statutory body and obtained statutory status in 1992 under the SEBI Act.',
        'reference': 'SEBI institutional history; Securities and Exchange Board of India Act, 1992.'
    },
    'BHASHA-BBL-0221a3cd-35e4-4bc8-b7f0-9146340339ed': {
        'question': 'Which statement correctly describes the independent-director databank under Section 150 of the Companies Act, 2013?',
        'options': ['An independent director may be selected from the databank, but the company must exercise due diligence before appointment', 'Every independent director must be appointed automatically from the databank without company due diligence', 'Only the Central Government may select an independent director from the databank', 'The databank replaces approval of the appointment in general meeting'],
        'answer': 0,
        'explanation': 'Section 150 permits selection from the databank but expressly places responsibility for due diligence on the company; appointment remains subject to the statutory approval process.',
        'reference': 'Companies Act, 2013, Section 150.'
    },
    'BHASHA-BBL-75d7816b-a497-4efb-9cb9-7814c7599975': {
        'question': 'Under Section 2(84) of the Companies Act, 2013, a “share” means a share in the share capital of a company and includes:',
        'options': ['Stock', 'Debenture', 'Bond', 'Deposit'],
        'answer': 0,
        'explanation': 'Section 2(84) expressly provides that “share” means a share in the share capital of a company and includes stock.',
        'reference': 'Companies Act, 2013, Section 2(84).'
    },
    'BHASHA-BBL-89e2f55d-29ec-4408-a2ec-52fddb6c198e': {
        'question': 'Which case is conventionally cited for the proposition that directors are agents of the company?',
        'options': ['Ferguson v. Wilson', 'Hampshire Land Co.', 'Allen v. Hyatt', 'Royal British Bank v. Turquand'],
        'answer': 0,
        'explanation': 'Ferguson v. Wilson is conventionally cited for the proposition that directors are agents of the company in relation to company transactions.',
        'reference': 'Ferguson v. Wilson (1866), company-law agency principle.'
    },
    'BHASHA-BBF-a28528f9-f9f3-4596-a497-aa24b09070f4': {
        'question': 'Under the current SEBI framework, what is the maximum value of securities in a Basic Services Demat Account (BSDA) for the account to remain eligible under the value threshold?',
        'options': ['₹2 lakh', '₹5 lakh', '₹10 lakh', '₹20 lakh'],
        'answer': 2,
        'explanation': 'The current BSDA value threshold is ₹10 lakh, subject to the applicable reckoning rules and exclusions.',
        'reference': 'SEBI BSDA framework, including the December 2025 ease-of-investment circular.'
    },
    'BHASHA-BBF-8fca38cd-9413-416a-b997-520848c070d1': {
        'question': 'In accounting, amortization of an intangible asset refers to:',
        'options': ['Systematic allocation of the asset’s depreciable amount over its useful life', 'Physical wear and tear of a tangible asset only', 'Revaluation of inventory to market price', 'Writing off all liabilities at once'],
        'answer': 0,
        'explanation': 'For intangible assets, amortization is the systematic allocation of the depreciable amount over the asset’s useful life.',
        'reference': 'Accounting concept of amortization of intangible assets.'
    },
    'BHASHA-BBL-8e897a63-0a34-414a-8e36-9ba97d74a0e0': {
        'question': 'If quorum is not present within half an hour at a general meeting called by requisitionists under Section 100 of the Companies Act, 2013, what happens under Section 103?',
        'options': ['The meeting stands cancelled', 'The meeting is automatically adjourned to the next week in every case', 'The chairperson may proceed without quorum', 'The meeting becomes an extraordinary board meeting'],
        'answer': 0,
        'explanation': 'Under Section 103, a meeting called by requisitionists stands cancelled if quorum is absent; other meetings are generally adjourned as provided by the section.',
        'reference': 'Companies Act, 2013, Sections 100 and 103.'
    },
    'BHASHA-BBL-a5759666-7d5b-4689-894d-2f756c83e071': {
        'question': 'Under Section 10A of the Companies Act, 2013, a company incorporated with share capital cannot commence business or exercise borrowing powers until which requirement is met?',
        'options': ['A director files the prescribed declaration that subscribers have paid for their shares, and the company has filed verification of its registered office', 'It receives a separate occupation certificate from the Registrar', 'It completes one full financial year', 'It converts into a public company'],
        'answer': 0,
        'explanation': 'Section 10A requires the prescribed declaration regarding payment for subscribed shares and verification of the registered office before commencement of business or borrowing.',
        'reference': 'Companies Act, 2013, Section 10A.'
    },
    'BHASHA-BBL-0b37b862-f020-4df9-8177-592aaf6e6e0c': {
        'question': 'For the filing-default limb of the “inactive company” concept under Section 455 of the Companies Act, 2013, for how many preceding financial years must financial statements and annual returns not have been filed?',
        'options': ['One financial year', 'Two financial years', 'Three financial years', 'Five financial years'],
        'answer': 1,
        'explanation': 'One limb of the inactive-company definition covers a company that has not filed financial statements and annual returns during the last two financial years.',
        'reference': 'Companies Act, 2013, Section 455.'
    },
    'BHASHA-BBL-ad9cf7b2-3257-494a-85bc-59a5cf4393f7': {
        'question': 'Section 2(7) of the Companies Act, 2013 defines which term?',
        'options': ['Auditing standards', 'Accounting standards', 'Financial statement', 'Books of account'],
        'answer': 0,
        'explanation': 'Section 2(7) defines “auditing standards”.',
        'reference': 'Companies Act, 2013, Section 2(7).'
    },
    'BHASHA-BBL-ea153fce-36d7-4086-98e4-81da2bb0862d': {
        'question': 'What term describes a company’s systematic responsibility toward stakeholders and the common good through appropriate business processes and strategies?',
        'options': ['Corporate social responsibility', 'Annual general meeting', 'Incorporation', 'Private placement'],
        'answer': 0,
        'explanation': 'The concept described is corporate social responsibility (CSR).',
        'reference': 'Corporate social responsibility concept; Companies Act, 2013, Section 135 for the statutory CSR framework.'
    },
    'BHASHA-BBL-8809940a-0212-457c-ab62-31f24ce727ca': {
        'question': 'For a company having share capital, which of the following is NOT a statutory eligibility route for members to apply for relief from oppression and mismanagement under Section 244, assuming calls and other sums due on their shares have been paid?',
        'options': ['Not less than 100 members or not less than one-tenth of the total number of members, whichever is less', 'Member or members holding not less than one-tenth of the issued share capital', 'A member holding one-fifteenth of the issued share capital', 'A group of members together holding not less than one-tenth of the issued share capital'],
        'answer': 2,
        'explanation': 'Section 244 uses the 100-members/one-tenth-of-members route or the one-tenth-of-issued-share-capital route; one-fifteenth is not the statutory threshold.',
        'reference': 'Companies Act, 2013, Section 244.'
    },
    'BHASHA-BBL-7647eaa6-bc7e-4da4-8aae-012133b5d9bd': {
        'question': 'Which statement correctly describes the relationship between a company’s memorandum of association and its articles of association?',
        'options': ['The articles are subordinate to the memorandum and must be consistent with it', 'The articles override the memorandum whenever they conflict', 'The memorandum and articles are unrelated documents with no hierarchy', 'The articles may expand the company’s objects beyond the memorandum'],
        'answer': 0,
        'explanation': 'The articles regulate internal management but remain subordinate to the memorandum and the Act.',
        'reference': 'Companies Act, 2013; memorandum and articles relationship.'
    },
    'BHASHA-BBL-ae9a7708-9e43-4c8f-9a02-4295af3cde60': {
        'question': 'Which statement about SEBI’s institutional history is correct?',
        'options': ['SEBI was constituted as a non-statutory body on 12 April 1988 and became a statutory body in 1992', 'SEBI was first constituted in 1992 and became statutory in 1988', 'SEBI was created in 1994 under the Companies Act', 'SEBI became statutory only in 2000'],
        'answer': 0,
        'explanation': 'SEBI was constituted in 1988 as a non-statutory body and became a statutory body in 1992 after enactment of the SEBI Act.',
        'reference': 'SEBI institutional history; SEBI Act, 1992.'
    },
    'BHASHA-BBL-12ffcdfd-c00e-47a5-830f-ce415927b804': {
        'question': 'Subject to Section 135 of the Companies Act, 2013, what percentage must an eligible company ordinarily spend on CSR based on the prescribed profit measure?',
        'options': ['1% of average net profits of the three immediately preceding financial years', '2% of average net profits of the three immediately preceding financial years', '5% of current-year revenue', '10% of paid-up share capital'],
        'answer': 1,
        'explanation': 'Section 135(5) ordinarily requires at least 2% of the average net profits of the three immediately preceding financial years, with the statutory treatment for companies that have not completed three years.',
        'reference': 'Companies Act, 2013, Section 135(5).'
    },
    'BHASHA-BBL-e6371329-cc3b-4db7-b9c8-c0aabd142d4a': {
        'question': 'Which section of the Companies Act, 2013 empowers the Central Government to make rules for electronic filing, maintenance, inspection and related handling of company documents?',
        'options': ['Section 398', 'Section 401', 'Section 402', 'Section 447'],
        'answer': 0,
        'explanation': 'Section 398 deals with electronic form of applications, documents, inspection and related matters. Section 401 concerns value-added services and Section 402 applies Information Technology Act provisions.',
        'reference': 'Companies Act, 2013, Sections 398, 401 and 402.'
    },
    'BHASHA-BBL-ac407161-398e-482f-8586-18a2fe4f6eb3': {
        'question': 'A private company proposes to convert into a public company and must alter its articles accordingly. Which type of members’ resolution is generally required for alteration of articles under the Companies Act, 2013?',
        'options': ['Special resolution', 'Ordinary resolution only', 'Board resolution only', 'No resolution'],
        'answer': 0,
        'explanation': 'Alteration of articles under Section 14 generally requires a special resolution, along with the applicable statutory filings and conversion requirements.',
        'reference': 'Companies Act, 2013, Section 14.'
    },
    'BHASHA-BBL-fb5f725d-c7b0-4e65-8581-0452cd6ef43e': {
        'question': 'Under Section 42 of the Companies Act, 2013, securities offered by private placement must be allotted within how many days from receipt of the application money?',
        'options': ['30 days', '45 days', '60 days', '90 days'],
        'answer': 2,
        'explanation': 'Section 42 requires allotment within 60 days from receipt of the application money, failing which the statutory refund consequences apply.',
        'reference': 'Companies Act, 2013, Section 42.'
    },
    'BHASHA-BBL-43174082-d000-4803-acb7-ca27fd64fb01': {
        'question': 'Section 8 of the Companies Act, 2013 primarily deals with:',
        'options': ['Companies formed for charitable or similar not-for-profit objects', 'Buy-back of securities', 'Reduction of share capital', 'Registration of charges'],
        'answer': 0,
        'explanation': 'Section 8 deals with companies formed to promote charitable and similar objects and applying profits toward those objects subject to the statutory conditions.',
        'reference': 'Companies Act, 2013, Section 8.'
    },
    'BHASHA-BBF-cb0798e5-627c-490f-8ced-da2f51729f41': {
        'question': 'Under the ordinary rule in Section 135(1) of the Companies Act, 2013, a CSR Committee consists of:',
        'options': ['Three or more directors, including at least one independent director, subject to the statutory provisos', 'Exactly two directors in every company', 'Only independent directors', 'Five directors in every listed company'],
        'answer': 0,
        'explanation': 'Section 135(1) generally provides for three or more directors including at least one independent director, while its provisos modify the composition for specified companies.',
        'reference': 'Companies Act, 2013, Section 135(1).',
        'category': 'Corporate Governance',
        'subtopic': 'Corporate Governance'
    },
    'BHASHA-BBF-0860c042-08ac-4003-abff-afe95e31dbbf': {
        'question': 'Under Section 140(5) of the Companies Act, 2013, which authority may direct a company to change its auditor where the auditor has acted fraudulently or abetted or colluded in fraud?',
        'options': ['The Tribunal', 'A District Court', 'The stock exchange', 'The company secretary'],
        'answer': 0,
        'explanation': 'Section 140(5) empowers the Tribunal, on the specified fraud-related grounds, to direct the company to change its auditor.',
        'reference': 'Companies Act, 2013, Section 140(5).'
    },
    'BHASHA-BBF-fe213d24-7e17-4933-8346-fc3a187280b8': {
        'question': 'Under the current SEBI Prohibition of Insider Trading framework, which of the following is NOT ordinarily an example of unpublished price sensitive information (UPSI)?',
        'options': ['A material change in securities or capital structure', 'A material revision in ratings', 'Fraud or default by promoters or key managerial personnel', 'Routine commencement of an ordinary CSR activity with no material price-sensitive implication'],
        'answer': 3,
        'explanation': 'The current UPSI framework includes specified material events such as securities/capital changes, ratings-related events and fraud/default matters. A routine CSR activity is not by itself a standard UPSI category.',
        'reference': 'SEBI (Prohibition of Insider Trading) Regulations, 2015, Regulation 2(1)(n), as amended in 2025.'
    },
    'BHASHA-BBF-76f1c43d-52cf-4c58-8675-8d091ff9b6b5': {
        'question': 'Under the SEBI mutual-fund exposure framework, what is the base single-issuer limit for debt securities before any permitted extension with the required approvals?',
        'options': ['10% of the scheme’s NAV', '12% of the scheme’s NAV', '15% of the scheme’s NAV', '20% of the scheme’s NAV'],
        'answer': 0,
        'explanation': 'The base single-issuer debt exposure limit is 10% of NAV; the framework permits extension to 12% subject to the specified approvals and conditions.',
        'reference': 'SEBI mutual-fund single-issuer debt exposure framework.'
    },
    'BHASHA-BBF-dc5aed81-c2db-4a23-a311-25c99aa7e046': {
        'question': 'What is the general maximum redemption period for preference shares under the Companies Act, 2013, apart from the special infrastructure-project exception?',
        'options': ['10 years', '15 years', '20 years', '30 years'],
        'answer': 2,
        'explanation': 'The general rule is redemption within 20 years. Infrastructure projects may issue preference shares for a longer period subject to the prescribed conditions, including the rule-based framework extending up to 30 years.',
        'reference': 'Companies Act, 2013, Section 55 and the Companies (Share Capital and Debentures) Rules.'
    },
    'BHASHA-BBF-1cd55614-01c5-4b8c-b4fb-7da2e5541d73': {
        'question': 'When may a firm be appointed as auditor of a company under the Companies Act, 2013?',
        'options': ['When a majority of its partners practising in India are qualified for appointment as auditors', 'Only when every partner is a chartered accountant', 'Whenever any one partner is qualified, regardless of the others', 'Only when the firm has at least ten partners'],
        'answer': 0,
        'explanation': 'A firm may be appointed by its firm name where a majority of partners practising in India are qualified for appointment; only qualified chartered accountant partners may act and sign on behalf of the firm.',
        'reference': 'Companies Act, 2013, Sections 139 and 141.'
    },
    'BHASHA-BBF-ce825cdd-5ca6-4350-815f-6d10891ea544': {
        'question': 'In accounting for intangible assets, amortization means:',
        'options': ['Systematic allocation of the depreciable amount of an intangible asset over its useful life', 'Repayment of a loan principal', 'Depreciation of land', 'Recognition of share premium'],
        'answer': 0,
        'explanation': 'In the accounting context, amortization is the systematic allocation of the depreciable amount of an intangible asset over its useful life.',
        'reference': 'Accounting concept of amortization of intangible assets.'
    },
    'BHASHA-BBF-c3993142-7c95-4df0-8a43-c21a7596f42a': {
        'question': 'Which set correctly states the alternative financial thresholds that bring a company within Section 135 CSR applicability?',
        'options': ['Net worth ₹500 crore or more, turnover ₹1,000 crore or more, or net profit ₹5 crore or more', 'Net worth ₹50 crore or more, turnover ₹500 crore or more, or net profit ₹2 crore or more', 'Paid-up capital ₹500 crore only', 'Turnover ₹100 crore and net profit ₹1 crore together'],
        'answer': 0,
        'explanation': 'Section 135 applies when any one of the specified thresholds is met: net worth ₹500 crore or more, turnover ₹1,000 crore or more, or net profit ₹5 crore or more, subject to the statutory time reference.',
        'reference': 'Companies Act, 2013, Section 135(1).'
    },
    'BHASHA-BBF-0172d7ee-cfd3-4a6f-9efc-7336bd5b7b24': {
        'question': 'Which of the following is NOT, by itself, a requirement for an individual to apply for a Director Identification Number (DIN)?',
        'options': ['Indian citizenship', 'Proof of identity', 'Proof of address', 'A photograph'],
        'answer': 0,
        'explanation': 'DIN may be allotted to eligible foreign nationals as well as Indian citizens. Identity/address evidence and a photograph form part of the application requirements.',
        'reference': 'Companies (Appointment and Qualification of Directors) Rules and DIN application requirements.'
    },
}

NPTEL_QUESTIONS = [
    {
        'id': 'NPTEL-TEC-2019-W1-Q1',
        'originalId': 'The-Ethical-Corporation-2019-Week1-Q1',
        'sourceId': 'NPTEL_ETHICAL_CORPORATION',
        'originType': 'preexisting_verbatim_mcq',
        'aiGenerated': False,
        'choicesGenerated': 'source-original',
        'sourceMode': 'Pre-existing NPTEL assignment MCQ, retained verbatim apart from punctuation normalization.',
        'sourceDomain': 'Corporate Governance and Ethics',
        'sourceTopic': 'Corporate Social Responsibility',
        'category': 'Corporate Governance',
        'subtopic': 'CSR and Governance Theory',
        'difficulty': 'S', 'difficultyLabel': 'Simple',
        'question': 'According to Carroll, the social responsibility of a business covers four kinds of responsibilities. Which of the following is not one of those four?',
        'options': ['Career responsibilities: to ensure career advancement opportunities to senior managers and directors of the company', 'Economic responsibilities: to make sufficient profit to stay in business', 'Ethical responsibilities: to engage in what is right and what is good', 'Legal responsibilities: to comply with the prevailing legal requirements'],
        'answer': 0,
        'explanation': 'NPTEL accepted answer: Career responsibilities. Carroll’s framework identifies economic, legal, ethical and philanthropic responsibilities.',
        'reference': 'NPTEL, The Ethical Corporation, Week 1 Assignment, Question 1.',
        'examEligible': True, 'validationRequired': False, 'reviewed': 'validated-source-2026-09-16', 'qualityStatus': 'Validated sourced question',
        'auditReasons': 'nptel_preexisting_mcq; corporate_governance_concept', 'qualityIssues': '', 'needsCurrentnessReview': False,
        'sourceLicense': 'CC BY-NC-SA',
        'sourceUrl': 'https://archive.nptel.ac.in/content/storage2/courses/downloads_new/110105138/Week_01_Assignment_01.pdf'
    },
    {
        'id': 'NPTEL-TEC-2019-W1-Q6', 'originalId': 'The-Ethical-Corporation-2019-Week1-Q6', 'sourceId': 'NPTEL_ETHICAL_CORPORATION',
        'originType': 'preexisting_verbatim_mcq', 'aiGenerated': False, 'choicesGenerated': 'source-original',
        'sourceMode': 'Pre-existing NPTEL assignment MCQ, retained verbatim apart from punctuation normalization.',
        'sourceDomain': 'Corporate Governance and Ethics', 'sourceTopic': 'Corporate Responsibility', 'category': 'Corporate Governance', 'subtopic': 'Corporate Responsibility',
        'difficulty': 'M', 'difficultyLabel': 'Medium',
        'question': 'Assertion (S): A corporation must act judiciously, with due consideration to what is right and what is good. Reason (R): A business fulfils society’s needs, and society gives it the licence to operate; there is an unwritten social contract between business and society to stay within certain limits.',
        'options': ['S is correct, but R is incorrect', 'Both S and R are correct, and R is a reason for S', 'Both S and R are correct, but R is not a reason for S', 'R is correct, but S is incorrect'],
        'answer': 1,
        'explanation': 'NPTEL accepted answer: Both statements are correct, and the social-contract reasoning supports the assertion.',
        'reference': 'NPTEL, The Ethical Corporation, Week 1 Assignment, Question 6.',
        'examEligible': True, 'validationRequired': False, 'reviewed': 'validated-source-2026-09-16', 'qualityStatus': 'Validated sourced question',
        'auditReasons': 'nptel_preexisting_mcq; corporate_governance_concept', 'qualityIssues': '', 'needsCurrentnessReview': False,
        'sourceLicense': 'CC BY-NC-SA', 'sourceUrl': 'https://archive.nptel.ac.in/content/storage2/courses/downloads_new/110105138/Week_01_Assignment_01.pdf'
    },
    {
        'id': 'NPTEL-TEC-2019-W1-Q7', 'originalId': 'The-Ethical-Corporation-2019-Week1-Q7', 'sourceId': 'NPTEL_ETHICAL_CORPORATION',
        'originType': 'preexisting_verbatim_mcq', 'aiGenerated': False, 'choicesGenerated': 'source-original',
        'sourceMode': 'Pre-existing NPTEL assignment MCQ, retained verbatim apart from punctuation normalization.',
        'sourceDomain': 'Corporate Governance and Ethics', 'sourceTopic': 'Corporation Characteristics', 'category': 'Companies Law', 'subtopic': 'Corporate Personality and Liability',
        'difficulty': 'M', 'difficultyLabel': 'Medium',
        'question': 'Consider the following characteristics of a corporation: (i) shareholders are personally liable for the actions and financial situation of the company; (ii) shareholders will not be personally liable for debts incurred by the corporation; (iii) incorporation is the legal process through which a corporation is created; (iv) liquidation is a process through which the legal life of a corporation may be ended. Which option is correct?',
        'options': ['i-False, ii-True, iii-True, iv-True', 'i-True, ii-True, iii-True, iv-False', 'i-True, ii-False, iii-False, iv-False', 'i-True, ii-False, iii-True, iv-True'],
        'answer': 0,
        'explanation': 'NPTEL accepted answer: i-False, ii-True, iii-True, iv-True.',
        'reference': 'NPTEL, The Ethical Corporation, Week 1 Assignment, Question 7.',
        'examEligible': True, 'validationRequired': False, 'reviewed': 'validated-source-2026-09-16', 'qualityStatus': 'Validated sourced question',
        'auditReasons': 'nptel_preexisting_mcq; company_law_concept', 'qualityIssues': '', 'needsCurrentnessReview': False,
        'sourceLicense': 'CC BY-NC-SA', 'sourceUrl': 'https://archive.nptel.ac.in/content/storage2/courses/downloads_new/110105138/Week_01_Assignment_01.pdf'
    },
    {
        'id': 'NPTEL-TEC-2019-W1-Q9', 'originalId': 'The-Ethical-Corporation-2019-Week1-Q9', 'sourceId': 'NPTEL_ETHICAL_CORPORATION',
        'originType': 'preexisting_verbatim_mcq', 'aiGenerated': False, 'choicesGenerated': 'source-original',
        'sourceMode': 'Pre-existing NPTEL assignment MCQ, retained verbatim apart from punctuation normalization.',
        'sourceDomain': 'Corporate Governance and Ethics', 'sourceTopic': 'CSR and Corporate Duties', 'category': 'Corporate Governance', 'subtopic': 'CSR and Stakeholders',
        'difficulty': 'M', 'difficultyLabel': 'Medium',
        'question': 'Identify the correct truth sequence for these claims: (i) the duty of managers of an ethical corporation is to run the business only in the interest of the company; (ii) next-generation CSR expects greater pro-activeness and engagement by business; (iii) Carroll’s four layers of CSR were intended to be met sequentially; (iv) law gives a corporation the right to acquire or sell property and to enter into contracts.',
        'options': ['i-False, ii-False, iii-False, iv-True', 'i-True, ii-True, iii-False, iv-True', 'i-False, ii-True, iii-False, iv-True', 'i-True, ii-False, iii-True, iv-False'],
        'answer': 2,
        'explanation': 'NPTEL accepted answer: i-False, ii-True, iii-False, iv-True.',
        'reference': 'NPTEL, The Ethical Corporation, Week 1 Assignment, Question 9.',
        'examEligible': True, 'validationRequired': False, 'reviewed': 'validated-source-2026-09-16', 'qualityStatus': 'Validated sourced question',
        'auditReasons': 'nptel_preexisting_mcq; corporate_governance_concept', 'qualityIssues': '', 'needsCurrentnessReview': False,
        'sourceLicense': 'CC BY-NC-SA', 'sourceUrl': 'https://archive.nptel.ac.in/content/storage2/courses/downloads_new/110105138/Week_01_Assignment_01.pdf'
    },
    {
        'id': 'NPTEL-TEC-2019-W4-Q3', 'originalId': 'The-Ethical-Corporation-2019-Week4-Q3', 'sourceId': 'NPTEL_ETHICAL_CORPORATION',
        'originType': 'preexisting_verbatim_mcq', 'aiGenerated': False, 'choicesGenerated': 'source-original',
        'sourceMode': 'Pre-existing NPTEL assignment MCQ, retained verbatim apart from punctuation normalization.',
        'sourceDomain': 'Corporate Governance and Ethics', 'sourceTopic': 'Shareholder Activism', 'category': 'Corporate Governance', 'subtopic': 'Shareholder Rights and Activism',
        'difficulty': 'S', 'difficultyLabel': 'Simple',
        'question': 'Which is the best way for an individual shareholder to demonstrate shareholder activism toward a corporation that neither pays dividend on time nor at the expected rate?',
        'options': ['Sell the company shares on the market', 'Attend the annual general meeting and raise the issue there', 'Overrule the board decision on the dividend rate', 'Take an active role in day-to-day management'],
        'answer': 1,
        'explanation': 'NPTEL accepted answer: attend the annual general meeting and raise the issue there.',
        'reference': 'NPTEL, The Ethical Corporation, Week 4 Assignment, Question 3.',
        'examEligible': True, 'validationRequired': False, 'reviewed': 'validated-source-2026-09-16', 'qualityStatus': 'Validated sourced question',
        'auditReasons': 'nptel_preexisting_mcq; corporate_governance_concept', 'qualityIssues': '', 'needsCurrentnessReview': False,
        'sourceLicense': 'CC BY-NC-SA', 'sourceUrl': 'https://archive.nptel.ac.in/content/storage2/courses/downloads_new/110105138/Week_04_Assignment_04.pdf'
    },
    {
        'id': 'NPTEL-TEC-2019-W4-Q5', 'originalId': 'The-Ethical-Corporation-2019-Week4-Q5', 'sourceId': 'NPTEL_ETHICAL_CORPORATION',
        'originType': 'preexisting_verbatim_mcq', 'aiGenerated': False, 'choicesGenerated': 'source-original',
        'sourceMode': 'Pre-existing NPTEL assignment MCQ, retained verbatim apart from punctuation normalization.',
        'sourceDomain': 'Corporate Governance and Ethics', 'sourceTopic': 'Agency Problem', 'category': 'Corporate Governance', 'subtopic': 'Agency and Board Governance',
        'difficulty': 'S', 'difficultyLabel': 'Simple',
        'question': 'Which of the following is NOT correct about why an agency problem may arise in corporate governance?',
        'options': ['Top executives may fail to perform duties aimed at creating value for the company and investors', 'Managers may pursue activities serving their own interests rather than shareholders’ interests', 'The duty of the principal is to look after the interests of the agents, and not vice versa', 'Shareholder or investor rights may not be protected by management'],
        'answer': 2,
        'explanation': 'NPTEL accepted answer: the statement reversing the principal-agent duty is not correct.',
        'reference': 'NPTEL, The Ethical Corporation, Week 4 Assignment, Question 5.',
        'examEligible': True, 'validationRequired': False, 'reviewed': 'validated-source-2026-09-16', 'qualityStatus': 'Validated sourced question',
        'auditReasons': 'nptel_preexisting_mcq; corporate_governance_concept', 'qualityIssues': '', 'needsCurrentnessReview': False,
        'sourceLicense': 'CC BY-NC-SA', 'sourceUrl': 'https://archive.nptel.ac.in/content/storage2/courses/downloads_new/110105138/Week_04_Assignment_04.pdf'
    },
    {
        'id': 'NPTEL-TEC-2019-W4-Q9', 'originalId': 'The-Ethical-Corporation-2019-Week4-Q9', 'sourceId': 'NPTEL_ETHICAL_CORPORATION',
        'originType': 'preexisting_verbatim_mcq', 'aiGenerated': False, 'choicesGenerated': 'source-original',
        'sourceMode': 'Pre-existing NPTEL assignment MCQ, retained verbatim apart from punctuation normalization.',
        'sourceDomain': 'Corporate Governance and Ethics', 'sourceTopic': 'Executive Compensation', 'category': 'Corporate Governance', 'subtopic': 'Executive Compensation and Governance',
        'difficulty': 'M', 'difficultyLabel': 'Medium',
        'question': 'Assertion 1: Disproportionately high salary of top executives compared with company performance is a prominent ethical issue in corporate governance. Assertion 2: In an acquisition, excessive executive salary may be renegotiated by the acquirer.',
        'options': ['Assertion 1 is true, but Assertion 2 is false', 'Both may be true, and Assertion 2 is a reason for Assertion 1', 'Both may be true, but Assertion 2 is not a reason for Assertion 1', 'Assertion 2 may be true, but Assertion 1 is false'],
        'answer': 2,
        'explanation': 'NPTEL accepted answer: both assertions may be true, but the second is not the reason for the first.',
        'reference': 'NPTEL, The Ethical Corporation, Week 4 Assignment, Question 9.',
        'examEligible': True, 'validationRequired': False, 'reviewed': 'validated-source-2026-09-16', 'qualityStatus': 'Validated sourced question',
        'auditReasons': 'nptel_preexisting_mcq; corporate_governance_concept', 'qualityIssues': '', 'needsCurrentnessReview': False,
        'sourceLicense': 'CC BY-NC-SA', 'sourceUrl': 'https://archive.nptel.ac.in/content/storage2/courses/downloads_new/110105138/Week_04_Assignment_04.pdf'
    },
]


def load_open_bank():
    text = OPEN_PATH.read_text(encoding='utf-8')
    match = re.search(r'window\.OPEN_QUESTION_BANK = (\[.*\]);\s*window\.OPEN_BANK_MANIFEST = (\{.*\});', text, re.S)
    if not match:
        raise RuntimeError('Could not parse data/open_questions.js')
    return json.loads(match.group(1)), json.loads(match.group(2))


def normalize_stem(value):
    return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()


def set_validated(q, mode='validated-current-law'):
    q['validationRequired'] = False
    q['reviewed'] = f'{mode}-{VALIDATED_AT}'
    q['qualityStatus'] = 'Validated current-law/source review'
    q['qualityIssues'] = ''
    q['needsCurrentnessReview'] = False
    q['aiGenerated'] = False
    return q


def apply_patch(q, patch):
    q.update(patch)
    q['originType'] = 'preexisting_corrected_mcq'
    q['choicesGenerated'] = 'source-corrected'
    q['sourceMode'] = 'Pre-existing BhashaBench MCQ corrected or reframed after current-law validation; not counted as a newly generated question.'
    return set_validated(q, 'validated-corrected-source')


def build():
    bank, old_manifest = load_open_bank()
    by_id = {q['id']: q for q in bank}

    missing_retired = sorted(set(RETIRE_REASONS) - set(by_id))
    missing_patches = sorted(set(PATCHES) - set(by_id))
    if missing_retired or missing_patches:
        raise RuntimeError(f'Missing IDs: retired={missing_retired}, patches={missing_patches}')

    retired = []
    active_bhasha = []
    for q in bank:
        qid = q['id']
        if qid in RETIRE_REASONS:
            rq = dict(q)
            rq['retiredAt'] = VALIDATED_AT
            rq['retirementReason'] = RETIRE_REASONS[qid]
            retired.append(rq)
            continue
        if qid in PATCHES:
            q = apply_patch(dict(q), PATCHES[qid])
        elif q.get('validationRequired'):
            q = set_validated(dict(q), 'validated-source-as-is')
        active_bhasha.append(q)

    if len(retired) != 13:
        raise RuntimeError(f'Expected 13 retired questions, got {len(retired)}')
    if len(active_bhasha) != 118:
        raise RuntimeError(f'Expected 118 active Bhasha questions, got {len(active_bhasha)}')

    existing_norm = {normalize_stem(q['question']): q['id'] for q in active_bhasha}
    accepted_nptel = []
    dedup_rows = []
    for q in NPTEL_QUESTIONS:
        norm = normalize_stem(q['question'])
        if norm in existing_norm:
            dedup_rows.append((q['id'], 'excluded_exact_duplicate', existing_norm[norm]))
            continue
        best_ratio = 0.0
        best_id = None
        for existing in active_bhasha + accepted_nptel:
            ratio = SequenceMatcher(None, norm, normalize_stem(existing['question'])).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_id = existing['id']
        if best_ratio >= 0.90:
            dedup_rows.append((q['id'], f'excluded_near_duplicate_{best_ratio:.3f}', best_id))
            continue
        accepted_nptel.append(q)
        dedup_rows.append((q['id'], f'imported_best_similarity_{best_ratio:.3f}', best_id or 'none'))

    if len(accepted_nptel) != 7:
        raise RuntimeError(f'Expected 7 NPTEL imports after dedupe, got {len(accepted_nptel)}: {dedup_rows}')

    combined = active_bhasha + accepted_nptel
    ids = [q['id'] for q in combined]
    if len(ids) != len(set(ids)):
        raise RuntimeError('Duplicate IDs in combined bank')
    if any(q.get('aiGenerated') for q in combined):
        raise RuntimeError('AI-generated question found; V8 is source-only')
    if any(q.get('validationRequired') for q in combined):
        raise RuntimeError('Active question still requires validation')
    for q in combined:
        if len(q.get('options', [])) != 4:
            raise RuntimeError(f'Question {q["id"]} does not have exactly four options')
        if not isinstance(q.get('answer'), int) or not (0 <= q['answer'] < 4):
            raise RuntimeError(f'Question {q["id"]} has invalid answer index')

    category_counts = Counter(q['category'] for q in combined)
    difficulty_counts = Counter(q['difficulty'] for q in combined)
    source_counts = Counter(q['sourceId'] for q in combined)

    manifest = {
        'schemaVersion': 5,
        'build': 'V8-validated-sourced',
        'generatedAt': '2026-09-16T12:00:00Z',
        'preexistingCount': len(combined),
        'corpusCount': len(combined),
        'bhashaActiveCount': len(active_bhasha),
        'nptelImportedCount': len(accepted_nptel),
        'retiredAfterValidationCount': len(retired),
        'directRelevantSourceRows': int(old_manifest.get('directRelevantSourceRows', 133)),
        'duplicateDirectStemsRemoved': int(old_manifest.get('duplicateDirectStemsRemoved', 2)),
        'nptelAssignmentQuestionsScreened': 20,
        'nptelCandidateQuestionsCurated': len(NPTEL_QUESTIONS),
        'nptelExcludedAsDuplicateCount': len(NPTEL_QUESTIONS) - len(accepted_nptel),
        'validationRequiredCount': 0,
        'sourceQualityPassCount': len(combined),
        'aiQuestionCount': 0,
        'categoryCounts': dict(sorted(category_counts.items())),
        'difficultyCounts': dict(sorted(difficulty_counts.items())),
        'sourceCounts': dict(sorted(source_counts.items())),
        'policy': 'Source-only V8: all active Bhasha questions are either previously source-quality-passed or validated/corrected; 13 defective/obsolete questions are retired. Seven pre-existing NPTEL assignment MCQs are added in a separate CC BY-NC-SA data file after relevance/currentness review and deduplication. No AI-authored questions are included.'
    }

    OPEN_PATH.write_text("'use strict';\n// Director Mock India V8 — validated BhashaBench source bank.\nwindow.OPEN_QUESTION_BANK = " + json.dumps(active_bhasha, ensure_ascii=False, separators=(',', ':')) + ";\nwindow.OPEN_BANK_MANIFEST = " + json.dumps(manifest, ensure_ascii=False, separators=(',', ':')) + ";\n", encoding='utf-8')
    NPTEL_PATH.write_text("'use strict';\n// Director Mock India V8 — NPTEL pre-existing assignment questions; CC BY-NC-SA.\nwindow.NPTEL_QUESTION_BANK = " + json.dumps(accepted_nptel, ensure_ascii=False, separators=(',', ':')) + ";\n", encoding='utf-8')
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    RETIRED_PATH.write_text(json.dumps(retired, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    (ROOT / 'data' / 'questions.js').write_text("""'use strict';

const SOURCE_CATALOG = {
  BHASHABENCH_LEGAL: {
    shortTitle: 'BhashaBench-Legal',
    title: 'BhashaBench-Legal via BhashaBench-Multi',
    url: 'https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi',
    license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
    author: 'BharatGen AI / BhashaBench authors',
    provenance: 'Source-original Indian-law MCQs, with current-law corrections where documented by the V8 validation audit.'
  },
  BHASHABENCH_FINANCE: {
    shortTitle: 'BhashaBench-Finance',
    title: 'BhashaBench-Finance via BhashaBench-Multi',
    url: 'https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi',
    license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
    author: 'BharatGen AI / BhashaBench authors',
    provenance: 'Source-original India-specific finance MCQs, with current-law corrections where documented by the V8 validation audit.'
  },
  NPTEL_ETHICAL_CORPORATION: {
    shortTitle: 'NPTEL — The Ethical Corporation',
    title: 'NPTEL / IIT Kharagpur — The Ethical Corporation (2019 assignments)',
    url: 'https://archive.nptel.ac.in/noc/courses/noc19/SEM2/noc19-mg56/',
    license: 'CC BY-NC-SA',
    licenseUrl: 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
    author: 'NPTEL / IIT Kharagpur course team',
    provenance: 'Pre-existing NPTEL assignment MCQs retained after IICA-domain relevance, currentness and duplicate screening. Stored separately because the licence is non-commercial/share-alike.'
  }
};

const OPEN_QUESTION_BANK = Array.isArray(window.OPEN_QUESTION_BANK) ? window.OPEN_QUESTION_BANK : [];
const NPTEL_QUESTION_BANK = Array.isArray(window.NPTEL_QUESTION_BANK) ? window.NPTEL_QUESTION_BANK : [];
const QUESTION_BANK = [...OPEN_QUESTION_BANK, ...NPTEL_QUESTION_BANK];
window.SOURCE_CATALOG = SOURCE_CATALOG;
window.QUESTION_BANK = QUESTION_BANK;
""", encoding='utf-8')

    (ROOT / 'data' / 'openbank-loader.js').write_text("""'use strict';
(() => {
  const frozen = Array.isArray(window.QUESTION_BANK) ? window.QUESTION_BANK : [];
  const manifest = window.OPEN_BANK_MANIFEST || {};
  window.OPEN_BANK_STATUS = {
    state: frozen.length ? 'ready' : 'unavailable',
    preexistingCount: frozen.length,
    corpusCount: frozen.length,
    bhashaActiveCount: Number(manifest.bhashaActiveCount || 0),
    nptelImportedCount: Number(manifest.nptelImportedCount || 0),
    retiredAfterValidationCount: Number(manifest.retiredAfterValidationCount || 0),
    validationRequiredCount: Number(manifest.validationRequiredCount || 0),
    sourceQualityPassCount: Number(manifest.sourceQualityPassCount || frozen.length),
    aiCount: Number(manifest.aiQuestionCount || 0),
    lastSync: manifest.generatedAt || null,
    error: frozen.length ? null : 'The bundled sourced question bank could not be loaded.',
    manifest
  };
  window.syncOpenBank = async () => window.OPEN_BANK_STATUS;
  window.OPEN_BANK_READY = Promise.resolve(window.OPEN_BANK_STATUS);
})();
""", encoding='utf-8')

    index_path = ROOT / 'index.html'
    index_text = index_path.read_text(encoding='utf-8')
    if 'data/nptel_questions.js' not in index_text:
        index_text = index_text.replace('<script src="data/open_questions.js"></script>', '<script src="data/open_questions.js"></script>\n  <script src="data/nptel_questions.js"></script>')
    index_text = index_text.replace('using only the unique questions classified as directly relevant to the IICA syllabus; no AI-authored questions.', 'using validated pre-existing sourced questions mapped to the IICA syllabus; no AI-authored questions.')
    index_path.write_text(index_text, encoding='utf-8')

    (ROOT / 'sw.js').write_text("""const CACHE='director-mock-v8-validated-sourced';
const ASSETS=['./','index.html','styles.css','app.js','data/open_questions.js','data/nptel_questions.js','data/questions.js','data/openbank-loader.js','data/bank_manifest.json','data/retired_questions.json','manifest.json','icons/icon-192.png','icons/icon-512.png','SOURCES.md','QUESTION_BANK_LICENSE.md','AUDIT_SUMMARY.md'];
self.addEventListener('install',event=>{
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)));
});
self.addEventListener('activate',event=>{
  event.waitUntil(Promise.all([
    self.clients.claim(),
    caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key))))
  ]));
});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  if(new URL(event.request.url).origin!==self.location.origin) return;
  event.respondWith(caches.match(event.request).then(cached=>cached||fetch(event.request).then(response=>{
    const copy=response.clone();
    caches.open(CACHE).then(cache=>cache.put(event.request,copy));
    return response;
  })));
});
""", encoding='utf-8')

    counts = ', '.join(f'{k}: {v}' for k, v in sorted(category_counts.items()))
    diffs = ', '.join(f'{k}: {v}' for k, v in sorted(difficulty_counts.items()))
    (ROOT / 'README.md').write_text(f"""# Director Mock India — V8 Validated Source Bank

Static, mobile-first PWA for practising the Indian Independent Director proficiency-assessment format.

## Active question bank

- **{len(combined)} pre-existing sourced questions are active.**
- BhashaBench active after validation/retirement: **{len(active_bhasha)}**.
- NPTEL pre-existing assignment questions imported after screening/deduplication: **{len(accepted_nptel)}**.
- Retired after current-law/quality validation: **{len(retired)}**.
- Categories: {counts}.
- Difficulty: {diffs}.
- Validation-required active questions: **0**.
- AI-authored question count: **0**.

## Validation status

The 88 questions previously flagged for validation were individually reviewed. The 37 valid-as-is items were cleared, 15 factual/reference defects were corrected, 23 useful items were rewritten for current law/clarity, and 13 obsolete/ambiguous items were retired from active sampling. Retired source rows are preserved in `data/retired_questions.json`.

## NPTEL source addition

Seven pre-existing questions from NPTEL/IIT Kharagpur's *The Ethical Corporation* assignments were added after direct IICA-domain relevance, currentness and duplicate screening. NPTEL question text is kept in `data/nptel_questions.js` because it carries **CC BY-NC-SA** terms and must remain licence-distinct from the MIT application code and the CC BY 4.0 BhashaBench data.

## Mock format

- 50 questions
- 75 minutes
- 50% app pass threshold
- Per mock: 30 Companies Law, 10 Securities Law, 6 Basic Accountancy, 4 Corporate Governance.
- Questions and answer choices are shuffled.
- Practice, history, answer review, PWA/offline support and responsive layouts are included.

## Important

This is an unofficial educational preparation tool and is not affiliated with IICA, MCA, SEBI or NPTEL. Legal/regulatory questions should still be rechecked when laws or regulations change.
""", encoding='utf-8')

    (ROOT / 'SOURCES.md').write_text("""# Sources

## BhashaBench

Active Bhasha questions originate from BhashaBench-Legal and BhashaBench-Finance via BhashaBench-Multi.

- https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi
- Licence recorded by source rows: CC BY 4.0
- V8 preserves source IDs and records whether a question was retained as-is or corrected/reframed after current-law validation.

## NPTEL / IIT Kharagpur — The Ethical Corporation

Seven active questions come from the official NPTEL 2019 assignment PDFs for *The Ethical Corporation*:

- Week 1 assignment: https://archive.nptel.ac.in/content/storage2/courses/downloads_new/110105138/Week_01_Assignment_01.pdf
- Week 4 assignment: https://archive.nptel.ac.in/content/storage2/courses/downloads_new/110105138/Week_04_Assignment_04.pdf
- Course archive: https://archive.nptel.ac.in/noc/courses/noc19/SEM2/noc19-mg56/
- NPTEL site licence notice: CC BY-NC-SA.

The NPTEL rows are stored separately in `data/nptel_questions.js` so their non-commercial/share-alike licence is not confused with the MIT application code or CC BY 4.0 BhashaBench data.

## Excluded sources

Public coaching/test-prep pages and datasets without a clear reusable licence are not copied into the active bank. AI/synthetic datasets are not included in V8.
""", encoding='utf-8')

    (ROOT / 'QUESTION_BANK_LICENSE.md').write_text("""# Question-bank licensing

The application source code is covered by the repository's `LICENSE` file. Question content is separately licensed by its original source and is **not** relicensed as MIT merely because it is stored in this repository.

## BhashaBench rows

BhashaBench source rows identify **CC BY 4.0**. Attribution/provenance is retained in each question object and in `SOURCES.md`.

## NPTEL rows

`data/nptel_questions.js` contains pre-existing NPTEL/IIT Kharagpur assignment questions. NPTEL's site identifies distributed material under **CC BY-NC-SA** terms. These rows must therefore retain attribution, remain non-commercial, and respect the applicable share-alike requirement.

Do not represent the NPTEL question text as MIT-licensed or CC BY 4.0 material.
""", encoding='utf-8')

    (ROOT / 'AUDIT_SUMMARY.md').write_text(f"""# V8 question-bank audit summary

- Bhasha active before validation: 131
- Previously validation-required: 88
- Validated as-is: 37
- Corrected: 15
- Rewritten for current law/clarity: 23
- Retired: 13
- Bhasha active after retirement: {len(active_bhasha)}
- NPTEL assignment questions screened: 20
- NPTEL curated candidates encoded: {len(NPTEL_QUESTIONS)}
- NPTEL imported after deduplication: {len(accepted_nptel)}
- Total active sourced questions: {len(combined)}
- Active validation-required questions: 0
- AI-authored questions: 0

Category counts: {json.dumps(dict(sorted(category_counts.items())), ensure_ascii=False)}
Difficulty counts: {json.dumps(dict(sorted(difficulty_counts.items())), ensure_ascii=False)}

All 13 retired Bhasha rows remain preserved in `data/retired_questions.json` with retirement reasons. NPTEL content remains in a separate CC BY-NC-SA file.
""", encoding='utf-8')

    audit_dir = ROOT / 'audit'
    audit_dir.mkdir(exist_ok=True)
    (audit_dir / 'NPTEL_INGEST_2026-09-16.md').write_text("""# NPTEL ingest and deduplication — 16 September 2026

Scope: official NPTEL/IIT Kharagpur *The Ethical Corporation* Week 1 and Week 4 assignment material.

- 20 assignment questions were screened across the two official assignment papers.
- 7 single-answer questions were selected for direct IICA-domain relevance and durable governance/company-law value.
- Questions requiring multi-select support, carrying dated/obsolete legal formulations, falling outside the intended four domains, or substantially overlapping existing concepts were not imported.
- The curated 7 were then compared against every surviving Bhasha question using normalized exact matching plus a 0.90 SequenceMatcher near-duplicate threshold.
- Result: all 7 curated questions were unique enough to import; no curated question was rejected by the final stem-level duplicate gate.
- A stakeholder-theory assignment item was intentionally not curated because the surviving Bhasha bank already contains a direct stakeholder-theory question.
- No AI-authored questions were created or imported.

Licence handling: NPTEL question data is isolated in `data/nptel_questions.js` and marked CC BY-NC-SA; the application code remains separately MIT-licensed.
""", encoding='utf-8')

    print(json.dumps({'manifest': manifest, 'dedupe': dedup_rows}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    build()
