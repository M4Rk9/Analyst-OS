# HDFC Bank / Larsen & Toubro / Tata decision packet

**Pending decision:** 255 conflict-free core facts, 15 source PDFs, 40 conflict keys withheld. No facts or sources are approved by generation or merge.

Catalog SHA-256: `520c66905ec178c2c5ed630d98fd92ac25d40dcfd1dda1a5a4cd653d41110c8f`.
Evidence SHA-256: `fd6100f8cba547ecc8da71300066e7cc776d4141c3c90c262762938f34602bb8`.

## Scope decision — required before approval

The proposed Tata mapping follows the original Tata Motors Limited legal entity into its renamed FY2026 entity, Tata Motors Passenger Vehicles Limited (TMPV). Accepting this packet must explicitly accept that mapping and its series break. It does not change the seeded ticker or authorize splicing in the new CV company. See [ENTITY_SCOPE_DECISION.md](ENTITY_SCOPE_DECISION.md). If that mapping is rejected, leave Tata FY2026 fact and source reviews pending and prepare a new scope-specific catalog.

Every observation is a reported consolidated number; INR crore is multiplied by 10,000,000 using Decimal. BS and closing cash are March 31 instants; P&L and CF are April-March durations. Comparative columns corroborate or flag conflicts; only current-year, conflict-free FY2022–FY2026 observations enter this packet. No averaged, adjusted, restated-preferred or fabricated values are introduced.

Core field coverage is limited to the configured statement rows. Bank income/deposits/borrowings are not industrial revenue/debt proxies. L&T finance costs exclude the separate financial-services finance-cost line. Group profit includes NCI and each report’s discontinued-operation scope; HDFC bank_owner_profit is after minority interest. Reported profit is not recurring profit or EBITDA. Aliases used by analytics are not assigned by this packet.

## Metric definitions

- **bank_advances** (instant): Reported consolidated bank advances as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `8a2f831123ce9406ddbce0de8c46613c0d2c7bbab97593ce7a19a5843f6f0d00`.
- **bank_balances_call_money** (instant): Reported consolidated bank balances call money as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `f3e8ae6d4c9557517709c5dbd78ce0c487b20c445bff81375d8600399df1648c`.
- **bank_borrowings** (instant): Reported consolidated bank borrowings as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `b4b2ce9c1d8ce229997f44eddccb64f9e389b5a5eb6a618a2a07ef0f4ae5fb26`.
- **bank_cash_rbi** (instant): Reported consolidated bank cash rbi as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `51d4b0907097a96bc67b6803ecac001b00867e015ffaf207136d8e52a8fc0b79`.
- **bank_closing_cash** (instant): HDFC cash-flow closing cash equivalents including RBI balances and bank balances/money at call and short notice, per cash-flow note. Not the BS cash/RBI component alone. Definition SHA-256: `5c23557b4c8d92938bc5c8e53ddb87df242d0970af6ebedae60aadd64d9595f4`.
- **bank_deposits** (instant): Reported consolidated bank deposits as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `aca516e1b10bfce23778af7344cadc2a853224f3ec7cbdb654404c4aace2773d`.
- **bank_interest_earned** (duration): Reported consolidated bank interest earned as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `688263cef48cbb6ebfe3931ed097b577d3ef2b3a348f36efb3b1bd40983633ec`.
- **bank_interest_expended** (duration): Reported consolidated bank interest expended as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `f3c7fd12ed8b0467fb9ddd2a760058337f3861d1b5d2c8a57640c5e7cb2b2490`.
- **bank_investments** (instant): Reported consolidated bank investments as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `95288ff72dc79048f121eccf428c70205dd5c4d08e1e0717c14b687a1ee42a49`.
- **bank_operating_expenses** (duration): Reported consolidated bank operating expenses as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `becbfd93f0ecc9ffe3660cd77e6e85ff0801d99a2e7b9a9e6be60420ab5474d6`.
- **bank_other_income** (duration): Reported consolidated bank other income as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `04906115e583c9f959198057834a9ff35d5ce3cf259a805876357dbaba91ffc1`.
- **bank_owner_profit** (duration): HDFC consolidated net profit attributable to the group after minority interest, as printed; excludes minority interest. Not consolidated profit before minority interest. Definition SHA-256: `dd041813ee1779da49d9548cf7d2ddb8758fd2c4bbe1bca5e5bf84b52805cd19`.
- **bank_reserves_surplus** (instant): Reported consolidated bank reserves surplus as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `fd581257a7194eb30747f22580013b58233ba0029ba2ea6cbee2589398c2df23`.
- **bank_share_capital** (instant): Reported consolidated bank share capital as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `e2f506fadbf0cf5c4ee8687cde19ec2974558652cecec23fd69389a954989000`.
- **bank_total_assets** (instant): Reported consolidated bank total assets as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `a2e4d9c6c3022f6196f6f17648372524da6d0ee50ffd21e36fe2cf52959b9089`.
- **bank_total_income** (duration): Reported consolidated bank total income as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `17b0bbc749887d34db1bd5216693e92f2d42999a3814e22923a55829f4d49070`.
- **cash_and_cash_equivalents** (instant): Reported consolidated cash and cash equivalents as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `f635a19097f2a1e7171cbc165d43fff2521cd65aebc5a64122198c1eb6cfcce3`.
- **cff** (duration): Reported consolidated cff as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `fe96cb68969c1ce47fe06dc91d4da5e644271dd40261233781f9f5899a80b913`.
- **cfi** (duration): Reported consolidated cfi as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `772c5bb2010467d79805cfab207fc4f1c116ea2478ffb2ba61b44fa3cb74873c`.
- **cfo** (duration): Reported consolidated cfo as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `4dc28894db1400498758dcf5aaef9759856cbf842bb95cdbf0372f6d89db1ba1`.
- **closing_cash** (instant): Reported consolidated closing cash as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `f42719663e58e008e365a5371e5b01debcea584cfd75b24354d88c736cbc47a6`.
- **current_assets** (instant): Reported consolidated current assets as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `4bf851452be262b24b1cea65ea318f8b2f82ac21102e44543263abf1fcb5bdc6`.
- **current_liabilities** (instant): Reported consolidated current liabilities as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `8e154fecf61db913d952d46f5c1f07e0025464ef3e9b9d5a7f23033a8f51b883`.
- **current_receivables** (instant): Reported consolidated current receivables as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `4f7575abe121f92c6b76e9a7da1c1a3a981334515c323bfeaa6efd09b340a628`.
- **finance_costs** (duration): Reported consolidated finance costs as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `511a61e2cb2063c34b11b924f87b3efd344a1d335686315e32838f57e32d085e`.
- **inventory** (instant): Reported consolidated inventory as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `1a484a379d1bb193d8ecc79f922361b8103159843cfdeae57b90d315851996eb`.
- **lt_corporate_finance_costs** (duration): L&T consolidated Finance costs line; excludes separately presented finance cost of financial services business and finance lease activity. Not total group interest or an EBITDA adjustment. Definition SHA-256: `3c14bbc3cbb04585bea5f6c7c3f2553b68da14dbf704ebe2648a07ffefefdcfb`.
- **lt_reported_revenue** (duration): L&T reported consolidated revenue from operations under the statement’s continuing/discontinued-operation scope. Do not treat different report scopes as comparable without the source notes. Definition SHA-256: `e0d19296079c01b408f693192f17641d0c447fc8c2cd525cfb467cdc97514f14`.
- **noncurrent_assets** (instant): Reported consolidated noncurrent assets as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `eb1211fbd2c7377a8d96e98600c52e13f728b3443357350b09366f4af4cb7054`.
- **noncurrent_liabilities** (instant): Reported consolidated noncurrent liabilities as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `bea00b4255f17347f2cdaf926ec9ebb9ed3053533ae3556953b72156abfcbf9c`.
- **other_equity** (instant): Reported consolidated other equity as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `cdfdfa835f467857dc90a1eb989b2fc0abc9547471fbd2526657c939d0b9eef0`.
- **other_income** (duration): Reported consolidated other income as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `e887a02bd4a59e0041e4451a12d1c4583223f3d025f34235481cfc18dd65eda4`.
- **profit_for_year** (duration): Reported consolidated profit for year as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `cb1a1edb76313afea7c9af518905f355c21413bb2ade707af39fd8aeb3d6af64`.
- **share_capital** (instant): Reported consolidated share capital as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `8c74f5dc30eb492e4e6b511256548fc944c8234376d3bfc9b97d9d284c048b5e`.
- **tata_reported_revenue** (duration): Reported consolidated total revenue from operations of the original Tata Motors legal entity, renamed TMPV in FY2026, under the packet’s PROPOSED entity-continuity mapping. Continuing/discontinued scope follows each original report; FY2026 has a demerger series break. No pro-forma or harmonized growth series. Definition SHA-256: `3a38032594d25a8f18d5ce752ee0637fdb2759dc0446fb1ef186c22dfb0c63f7`.
- **total_assets** (instant): Reported consolidated total assets as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `b82fffbd176d1528c6c0ae2a395624d70fc0972175ac8ab5f79aaec2da9a2845`.
- **total_equity** (instant): Reported consolidated total equity as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `d8dbf18b5551a9b9dd459c9b9decdf3d8f14f54fa6be5f6901a9cfc4224790b3`.
- **total_equity_liabilities** (instant): Reported consolidated total equity liabilities as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `a444e79cdfa978667422d5d6b6b67bc85c8e0c1fe5e4b5ce8df5b92bba898e6c`.
- **total_expenses** (duration): Reported consolidated total expenses as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `b44ee02f547da19059045a6659ee1baa90a3a8fe510fc2a8bd36a33f250a76aa`.
- **total_income** (duration): Reported consolidated total income as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `43dc7d7fb604f5c1f4f62e4502936900af1592419da8db1054e24c37bbeba865`.
- **total_liabilities** (instant): Reported consolidated total liabilities as printed in the specified statement; signed INR crore. No derived proxy. Definition SHA-256: `12276c1f8f20e8f97f4fc6997d0ee614fa9adaafcba374eb2a323f1e40214aef`.

## Pinned primary source documents

PDF page numbers are one-based and include exchange-cover sheets. A ZIP source link opens the filing archive; extract only the named PDF member in the manifest. Do not append a PDF page fragment to a ZIP URL.

- **hdfc-bank FY2022**: [Integrated Annual Report 2021-22](https://nsearchives.nseindia.com/annual_reports/AR_20085_HDFCBANK_2021_2022_21062022163130_06212022170003.zip); PDF `hdfc-bank_2022_nse.pdf`, 8607805 bytes, 443 pages, SHA-256 `c4238074fceef5757349c76ce4f9aee9a01bad8f79cd5e179e15a6234e712338`. Archive member: `AR_20085_HDFCBANK_2021_2022_21062022163130.pdf`; transport SHA-256 `62268cfec3e5cda6e0134e06a85acd80b109e48b8add06fe5e3ada18211118cf`.
- **hdfc-bank FY2023**: [Integrated Annual Report 2022-23](https://nsearchives.nseindia.com/annual_reports/AR_22445_HDFCBANK_2022_2023_19072023141052_07192023150000.zip); PDF `hdfc-bank_2023_nse.pdf`, 10065136 bytes, 470 pages, SHA-256 `6e008a43c6fd4576e2f2e1e5b42dcff343dfa76bda5c9d6518f5027be576810d`. Archive member: `AR_22445_HDFCBANK_2022_2023_19072023141052.pdf`; transport SHA-256 `111bdb103d58ea9f607a3d40166ed231ff6c1bb56f244dab16ab6eb317fb3026`.
- **hdfc-bank FY2024**: [Integrated Annual Report 2023-24](https://nsearchives.nseindia.com/annual_reports/AR_24576_HDFCBANK_2023_2024_18072024183453.pdf); PDF `hdfc-bank_2024_nse.pdf`, 17350949 bytes, 610 pages, SHA-256 `fcd7ef37de26997fed3bcf2b7cfb9eb90f08d4e2617f5f3f967a1ac621c2a73e`.
- **hdfc-bank FY2025**: [Integrated Annual Report 2024-25 (revised)](https://nsearchives.nseindia.com/annual_reports/AR_27115_HDFCBANK_2024_2025_U_25072025220054.pdf); PDF `hdfc-bank_2025_revised.pdf`, 11762184 bytes, 591 pages, SHA-256 `875360e8667a46c33d0e33859b4cf363a6cdf68754e3220db9ce77b62fae434a`.
- **hdfc-bank FY2026**: [Integrated Annual Report 2025-26](https://nsearchives.nseindia.com/annual_reports/AR_29735_HDFCBANK_2025_2026_A_12667766_11072026001055.pdf); PDF `hdfc-bank_2026_nse.pdf`, 12667766 bytes, 678 pages, SHA-256 `92de3c75b6fc05afe8731e97705c9d3534cc192e677af02f4b325e3d82eafca6`.
- **larsen-toubro FY2022**: [Integrated Annual Report 2021-22](https://investors.larsentoubro.com/upload/AnnualRep/FY2022AnnualRepL%26T%20Annual%20Report%202021-22.pdf); PDF `larsen-toubro_2022.pdf`, 23855220 bytes, 628 pages, SHA-256 `f127e5a6b13601376ba6ff0ad0a6073308cca3c3b4c7ff4b2efa049fdd4f3d9d`.
- **larsen-toubro FY2023**: [Integrated Annual Report 2022-23](https://investors.larsentoubro.com/upload/AnnualRep/FY2023AnnualRepLT%20Integrated%20Annual%20Report%202023.pdf); PDF `larsen-toubro_2023.pdf`, 19210417 bytes, 700 pages, SHA-256 `410c3010df8c34b0d70872c42a938257a5581e63edbde649f7ccfb53dd211585`.
- **larsen-toubro FY2024**: [Integrated Annual Report 2023-24](https://investors.larsentoubro.com/upload/AnnualRep/FY2024AnnualRepLnT%20IAR24.pdf); PDF `larsen-toubro_2024.pdf`, 18694630 bytes, 668 pages, SHA-256 `012acee24d17d429fe5787db91df2c64f1cce88e1c0c3bcd70679712ece4c483`.
- **larsen-toubro FY2025**: [Integrated Annual Report 2024-25](https://investors.larsentoubro.com/upload/AnnualRep/FY2025AnnualRepL%26T-ANNUAL%20REPORT%202024-25%20-%20LOW%202.pdf); PDF `larsen-toubro_2025.pdf`, 21021004 bytes, 738 pages, SHA-256 `7db5b698f798ab63a4abebc2dbd8b1f107d64168b9d290259639e5540f38aa65`.
- **larsen-toubro FY2026**: [Integrated Annual Report 2025-26](https://investors.larsentoubro.com/upload/AnnualRep/FY2026AnnualRepLNTIARFY2026.pdf); PDF `larsen-toubro_2026.pdf`, 42055756 bytes, 754 pages, SHA-256 `e356bc6534fd2afe33bf11ad075a45e437c4ecb643ec2af39f9853f44cefe8a1`.
- **tata-motors FY2022**: [Integrated Annual Report 2021-22](https://static-assets.tatamotors.com/Production/www-tatamotors-com-NEW/wp-content/uploads/2023/12/annual-report-2021-22-1.pdf); PDF `tata-motors_2022.pdf`, 7893873 bytes, 446 pages, SHA-256 `2d7c3bfb4807d7d232e3cd6c9599ff6f25ae3b01925e680a9b4dc8dcc21c1db8`.
- **tata-motors FY2023**: [Integrated Annual Report 2022-23](https://nsearchives.nseindia.com/annual_reports/AR_22007_TATAMOTORS_2022_2023_12062023215502_06122023220000.zip); PDF `tata-motors_2023_nse.pdf`, 11843273 bytes, 529 pages, SHA-256 `21d90544da8893c592b9dfc06d7bb74e31f18e4981e8b3a7d576b92f45fd305c`. Archive member: `AR_22007_TATAMOTORS_2022_2023_12062023215502.pdf`; transport SHA-256 `165a4b0f7655f5666d8a4374bb74d61a61bb296f81e8f9461ea5ba9817401741`.
- **tata-motors FY2024**: [Integrated Annual Report 2023-24](https://www.tatamotors.com/financials/79-ar-html/pdf/tata-motor-IAR-2023-24.pdf); PDF `tata-motors_2024.pdf`, 20590964 bytes, 530 pages, SHA-256 `db02424e0ed1620452e32df320a540f923bf837193e5896757d27e27d24efd48`.
- **tata-motors FY2025**: [Integrated Annual Report 2024-25](https://nsearchives.nseindia.com/annual_reports/AR_27753_TATAMOTORS_2024_2025_A_29318961_26082025223051.pdf); PDF `tata-motors_2025_nse.pdf`, 29318961 bytes, 591 pages, SHA-256 `66eeb401f27cc674443aba27d949bca0231ac405e0dc10aae189096da78466c1`.
- **tata-motors FY2026**: [81st Integrated Annual Report 2025-26](https://nsearchives.nseindia.com/annual_reports/AR_29395_TMPV_2025_2026_A_21445169_15062026215933.pdf); PDF `tata-motors_2026_tmpv.pdf`, 21445169 bytes, 585 pages, SHA-256 `88bf67991efaa3f1e5330c67fffde7c2232465f5c7af1478098babbea2af9778`.

## hdfc-bank: 93 candidate facts

| Exact observation ID | Printed INR crore | PDF page | Printed label |
|---|---:|---:|---|
| `hdfc-bank:2022:bank_share_capital:report2022` | 554.55 | 322 | Capital |
| `hdfc-bank:2022:bank_reserves_surplus:report2022` | 246,771.62 | 322 | Reserves and surplus |
| `hdfc-bank:2022:bank_deposits:report2022` | 1,558,003.03 | 322 | Deposits |
| `hdfc-bank:2022:bank_borrowings:report2022` | 226,966.50 | 322 | Borrowings |
| `hdfc-bank:2022:bank_advances:report2022` | 1,420,942.28 | 322 | Advances |
| `hdfc-bank:2022:bank_investments:report2022` | 449,263.86 | 322 | Investments |
| `hdfc-bank:2022:bank_cash_rbi:report2022` | 130,030.71 | 322 | Cash and balances with Reserve Bank of India |
| `hdfc-bank:2022:bank_balances_call_money:report2022` | 25,355.02 | 322 | Balances with banks and money at call and short notice |
| `hdfc-bank:2022:bank_total_assets:report2022` | 2,122,934.30 | 322 | Total |
| `hdfc-bank:2022:bank_interest_earned:report2022` | 135,936.41 | 323 | Interest earned |
| `hdfc-bank:2022:bank_other_income:report2022` | 31,758.99 | 323 | Other income |
| `hdfc-bank:2022:bank_total_income:report2022` | 167,695.40 | 323 | Total |
| `hdfc-bank:2022:bank_interest_expended:report2022` | 58,584.33 | 323 | Interest expended |
| `hdfc-bank:2022:bank_operating_expenses:report2022` | 40,312.43 | 323 | Operating expenses |
| `hdfc-bank:2022:bank_owner_profit:report2022` | 38,052.75 | 323 | Consolidated Net Profit for the year attributable to the group |
| `hdfc-bank:2022:cfo:report2022` | (11,959.57) | 324 | Net cash flow (used in) / from operating activities |
| `hdfc-bank:2022:cfi:report2022` | (2,216.33) | 324 | Net cash flow used in investing activities |
| `hdfc-bank:2022:cff:report2022` | 48,124.02 | 324 | Net cash flow from / (used in) financing activities |
| `hdfc-bank:2022:bank_closing_cash:report2022` | 155,385.73 | 324 | Cash and cash equivalents as at March 31st |
| `hdfc-bank:2023:bank_share_capital:report2023` | 557.97 | 338 | Capital |
| `hdfc-bank:2023:bank_deposits:report2023` | 1,882,663.25 | 338 | Deposits |
| `hdfc-bank:2023:bank_borrowings:report2023` | 256,548.66 | 338 | Borrowings |
| `hdfc-bank:2023:bank_advances:report2023` | 1,661,949.29 | 338 | Advances |
| `hdfc-bank:2023:bank_investments:report2023` | 511,581.71 | 338 | Investments |
| `hdfc-bank:2023:bank_cash_rbi:report2023` | 117,189.28 | 338 | Cash and balances with Reserve Bank of India |
| `hdfc-bank:2023:bank_balances_call_money:report2023` | 79,958.53 | 338 | Balances with banks and money at call and short notice |
| `hdfc-bank:2023:bank_total_assets:report2023` | 2,530,432.44 | 338 | Total |
| `hdfc-bank:2023:bank_interest_earned:report2023` | 170,754.05 | 339 | Interest earned |
| `hdfc-bank:2023:bank_other_income:report2023` | 33,912.05 | 339 | Other income |
| `hdfc-bank:2023:bank_total_income:report2023` | 204,666.10 | 339 | Total |
| `hdfc-bank:2023:bank_interest_expended:report2023` | 77,779.94 | 339 | Interest expended |
| `hdfc-bank:2023:bank_operating_expenses:report2023` | 51,533.69 | 339 | Operating expenses |
| `hdfc-bank:2023:bank_owner_profit:report2023` | 45,997.11 | 339 | Consolidated Net Profit for the year attributable to the group |
| `hdfc-bank:2023:cfo:report2023` | 20,813.70 | 340 | Net cash flows from / (used in) operating activities |
| `hdfc-bank:2023:cfi:report2023` | (3,423.89) | 340 | Net cash flow used in investing activities |
| `hdfc-bank:2023:cff:report2023` | 23,940.56 | 340 | Net cash flow from financing activities |
| `hdfc-bank:2023:bank_closing_cash:report2023` | 197,147.81 | 340 | Cash and cash equivalents as at the year end (Schedule 6 + 7) |
| `hdfc-bank:2024:bank_share_capital:report2024` | 759.69 | 437 | Capital |
| `hdfc-bank:2024:bank_reserves_surplus:report2024` | 452,982.84 | 437 | Reserves and surplus |
| `hdfc-bank:2024:bank_deposits:report2024` | 2,376,887.28 | 437 | Deposits |
| `hdfc-bank:2024:bank_borrowings:report2024` | 730,615.46 | 437 | Borrowings |
| `hdfc-bank:2024:bank_investments:report2024` | 1,005,681.63 | 437 | Investments |
| `hdfc-bank:2024:bank_cash_rbi:report2024` | 178,718.67 | 437 | Cash and balances with Reserve Bank of India |
| `hdfc-bank:2024:bank_balances_call_money:report2024` | 50,115.84 | 437 | Balances with banks and money at call and short notice |
| `hdfc-bank:2024:bank_total_assets:report2024` | 4,030,194.26 | 437 | Total |
| `hdfc-bank:2024:bank_interest_earned:report2024` | 283,649.02 | 438 | Interest earned |
| `hdfc-bank:2024:bank_other_income:report2024` | 124,345.75 | 438 | Other income |
| `hdfc-bank:2024:bank_total_income:report2024` | 407,994.77 | 438 | Total |
| `hdfc-bank:2024:bank_interest_expended:report2024` | 154,138.55 | 438 | Interest expended |
| `hdfc-bank:2024:bank_operating_expenses:report2024` | 152,269.34 | 438 | Operating expenses |
| `hdfc-bank:2024:bank_owner_profit:report2024` | 64,062.04 | 438 | Consolidated Net Profit for the year attributable to the group |
| `hdfc-bank:2024:cfo:report2024` | 19,069.34 | 439 | Net cash flows from operating activities |
| `hdfc-bank:2024:cfi:report2024` | 5,313.77 | 439 | Net cash flow from / (used) in investing activities |
| `hdfc-bank:2024:cff:report2024` | (3,983.06) | 440 | Net cash flow (used) / from financing activities |
| `hdfc-bank:2024:bank_closing_cash:report2024` | 228,834.51 | 440 | Cash and cash equivalents at the end of the year |
| `hdfc-bank:2025:bank_share_capital:report2025` | 765.22 | 442 | Capital |
| `hdfc-bank:2025:bank_reserves_surplus:report2025` | 517,218.98 | 442 | Reserves and surplus |
| `hdfc-bank:2025:bank_deposits:report2025` | 2,710,898.23 | 442 | Deposits |
| `hdfc-bank:2025:bank_borrowings:report2025` | 634,605.57 | 442 | Borrowings |
| `hdfc-bank:2025:bank_advances:report2025` | 2,724,938.16 | 442 | Advances |
| `hdfc-bank:2025:bank_investments:report2025` | 1,186,472.89 | 442 | Investments |
| `hdfc-bank:2025:bank_cash_rbi:report2025` | 144,390.25 | 442 | Cash and balances with Reserve Bank of India |
| `hdfc-bank:2025:bank_balances_call_money:report2025` | 105,557.65 | 442 | Balances with banks and money at call and short notice |
| `hdfc-bank:2025:bank_total_assets:report2025` | 4,392,417.42 | 442 | Total |
| `hdfc-bank:2025:bank_interest_earned:report2025` | 336,367.43 | 443 | Interest earned |
| `hdfc-bank:2025:bank_other_income:report2025` | 134,548.50 | 443 | Other income |
| `hdfc-bank:2025:bank_total_income:report2025` | 470,915.93 | 443 | Total |
| `hdfc-bank:2025:bank_interest_expended:report2025` | 183,894.20 | 443 | Interest expended |
| `hdfc-bank:2025:bank_operating_expenses:report2025` | 176,605.07 | 443 | Operating expenses |
| `hdfc-bank:2025:bank_owner_profit:report2025` | 70,792.25 | 443 | Consolidated Net Profit for the year attributable to the group |
| `hdfc-bank:2025:cfo:report2025` | 127,241.84 | 444 | Net cash flows from operating activities |
| `hdfc-bank:2025:cfi:report2025` | (3,850.64) | 444 | Net cash flow from / (used in) investing activities |
| `hdfc-bank:2025:cff:report2025` | (102,477.54) | 445 | Net cash flow used in financing activities |
| `hdfc-bank:2025:bank_closing_cash:report2025` | 249,947.90 | 445 | Cash and cash equivalents at the end of the year |
| `hdfc-bank:2026:bank_share_capital:report2026` | 1,539.34 | 496 | Capital |
| `hdfc-bank:2026:bank_reserves_surplus:report2026` | 579,975.02 | 496 | Reserves and surplus |
| `hdfc-bank:2026:bank_deposits:report2026` | 3,099,638.29 | 496 | Deposits |
| `hdfc-bank:2026:bank_borrowings:report2026` | 588,484.55 | 496 | Borrowings |
| `hdfc-bank:2026:bank_advances:report2026` | 3,050,783.23 | 496 | Advances |
| `hdfc-bank:2026:bank_investments:report2026` | 1,280,216.29 | 496 | Investments |
| `hdfc-bank:2026:bank_cash_rbi:report2026` | 200,707.11 | 496 | Cash and balances with Reserve Bank of India |
| `hdfc-bank:2026:bank_balances_call_money:report2026` | 111,218.94 | 496 | Balances with banks and money at call and short notice |
| `hdfc-bank:2026:bank_total_assets:report2026` | 4,908,040.84 | 496 | Total |
| `hdfc-bank:2026:bank_interest_earned:report2026` | 348,615.15 | 497 | Interest earned |
| `hdfc-bank:2026:bank_other_income:report2026` | 146,847.66 | 497 | Other income |
| `hdfc-bank:2026:bank_total_income:report2026` | 495,462.81 | 497 | Total |
| `hdfc-bank:2026:bank_interest_expended:report2026` | 185,491.23 | 497 | Interest expended |
| `hdfc-bank:2026:bank_operating_expenses:report2026` | 181,173.91 | 497 | Operating expenses |
| `hdfc-bank:2026:bank_owner_profit:report2026` | 76,025.97 | 497 | Consolidated Net Profit for the year attributable to the group |
| `hdfc-bank:2026:cfo:report2026` | 113,506.38 | 498 | Net cash flows from operating activities |
| `hdfc-bank:2026:cfi:report2026` | 6,362.72 | 498 | Net cash flow from / (used in) investing activities |
| `hdfc-bank:2026:cff:report2026` | (59,004.85) | 499 | Net cash flow used in financing activities |
| `hdfc-bank:2026:bank_closing_cash:report2026` | 311,926.05 | 499 | Cash and cash equivalents at the end of the year |

## larsen-toubro: 99 candidate facts

| Exact observation ID | Printed INR crore | PDF page | Printed label |
|---|---:|---:|---|
| `larsen-toubro:2022:cash_and_cash_equivalents:report2022` | 13770.24 | 496 | Cash and cash equivalents |
| `larsen-toubro:2022:inventory:report2022` | 5943.32 | 496 | Inventories |
| `larsen-toubro:2022:share_capital:report2022` | 281.01 | 497 | Equity share capital |
| `larsen-toubro:2022:other_equity:report2022` | 82126.65 | 497 | Other equity |
| `larsen-toubro:2022:total_equity:report2022` | 95373.73 | 497 | TOTAL EQUITY |
| `larsen-toubro:2022:lt_reported_revenue:report2022` | 156521.23 | 498 | Revenue from operations |
| `larsen-toubro:2022:other_income:report2022` | 2267.08 | 498 | Other income (net) |
| `larsen-toubro:2022:total_income:report2022` | 158788.31 | 498 | Total Income |
| `larsen-toubro:2022:lt_corporate_finance_costs:report2022` | 3125.70 | 498 | Finance costs |
| `larsen-toubro:2022:profit_for_year:report2022` | 10419.24 | 498 | Net profit after tax from continuing operations & discontinued operations |
| `larsen-toubro:2022:cfo:report2022` | 19163.58 | 502 | Net cash (used in)/from operating activities |
| `larsen-toubro:2022:cfi:report2022` | (3667.68) | 502 | Net cash (used in)/from investing activities |
| `larsen-toubro:2022:cff:report2022` | (15181.48) | 503 | Net cash (used in)/from financing activities |
| `larsen-toubro:2022:closing_cash:report2022` | 13770.24 | 503 | Cash and cash equivalents at end of the year [Note 14] |
| `larsen-toubro:2023:total_assets:report2023` | 330352.31 | 568 | TOTAL ASSETS |
| `larsen-toubro:2023:cash_and_cash_equivalents:report2023` | 16926.69 | 568 | Cash and cash equivalents |
| `larsen-toubro:2023:inventory:report2023` | 6828.78 | 568 | Inventories |
| `larsen-toubro:2023:current_receivables:report2023` | 44731.53 | 568 | Trade receivables |
| `larsen-toubro:2023:share_capital:report2023` | 281.10 | 569 | Equity share capital |
| `larsen-toubro:2023:other_equity:report2023` | 89044.85 | 569 | Other equity |
| `larsen-toubro:2023:total_equity_liabilities:report2023` | 330352.31 | 569 | TOTAL EQUITY AND LIABILITIES |
| `larsen-toubro:2023:noncurrent_assets:report2023` | 108147.99 | 568 | Sub-total - Non-current assets |
| `larsen-toubro:2023:current_assets:report2023` | 221215.52 | 568 | Sub-total - Current assets |
| `larsen-toubro:2023:total_equity:report2023` | 103567.22 | 569 | TOTAL EQUITY |
| `larsen-toubro:2023:total_liabilities:report2023` | 226785.09 | 569 | TOTAL LIABILITIES |
| `larsen-toubro:2023:current_liabilities:report2023` | 162065.99 | 569 | Sub-total - Current liabilities |
| `larsen-toubro:2023:noncurrent_liabilities:report2023` | 64719.10 | 569 | Sub-total - Non-current liabilities |
| `larsen-toubro:2023:lt_reported_revenue:report2023` | 183340.70 | 570 | Revenue from operations |
| `larsen-toubro:2023:other_income:report2023` | 2929.17 | 570 | Other income (net) |
| `larsen-toubro:2023:total_income:report2023` | 186269.87 | 570 | Total Income |
| `larsen-toubro:2023:lt_corporate_finance_costs:report2023` | 3207.16 | 570 | Finance costs |
| `larsen-toubro:2023:total_expenses:report2023` | 169296.83 | 570 | Total Expenses |
| `larsen-toubro:2023:profit_for_year:report2023` | 12530.62 | 570 | Profit for the year |
| `larsen-toubro:2023:cfo:report2023` | 22776.96 | 574 | Net cash from operating activities |
| `larsen-toubro:2023:cfi:report2023` | (8311.70) | 574 | Net cash used in investing activities |
| `larsen-toubro:2023:cff:report2023` | (11572.49) | 575 | Net cash used in financing activities |
| `larsen-toubro:2023:closing_cash:report2023` | 16926.69 | 575 | Cash and cash equivalents at end of the year [Note 14] |
| `larsen-toubro:2024:cash_and_cash_equivalents:report2024` | 11958.50 | 526 | Cash and cash equivalents |
| `larsen-toubro:2024:inventory:report2024` | 6620.19 | 526 | Inventories |
| `larsen-toubro:2024:current_receivables:report2024` | 48770.95 | 526 | Trade receivables |
| `larsen-toubro:2024:share_capital:report2024` | 274.93 | 527 | Equity share capital |
| `larsen-toubro:2024:other_equity:report2024` | 86084.31 | 527 | Other equity |
| `larsen-toubro:2024:noncurrent_assets:report2024` | 121547.37 | 526 | Sub-total - Non-current assets |
| `larsen-toubro:2024:total_equity:report2024` | 102549.66 | 527 | TOTAL EQUITY |
| `larsen-toubro:2024:noncurrent_liabilities:report2024` | 60476.85 | 527 | Sub-total - Non-current liabilities |
| `larsen-toubro:2024:lt_reported_revenue:report2024` | 221112.91 | 528 | Revenue from operations |
| `larsen-toubro:2024:other_income:report2024` | 4158.03 | 528 | Other income (net) |
| `larsen-toubro:2024:total_income:report2024` | 225270.94 | 528 | Total Income |
| `larsen-toubro:2024:lt_corporate_finance_costs:report2024` | 3545.85 | 528 | Finance costs |
| `larsen-toubro:2024:total_expenses:report2024` | 204847.44 | 528 | Total Expenses |
| `larsen-toubro:2024:profit_for_year:report2024` | 15547.10 | 528 | Profit for the year |
| `larsen-toubro:2024:cfo:report2024` | 18266.28 | 532 | Net cash generated from operating activities |
| `larsen-toubro:2024:cfi:report2024` | 2163.04 | 532 | Net cash generated from/(used in) investing activities |
| `larsen-toubro:2024:cff:report2024` | (25413.36) | 533 | Net cash used in financing activities |
| `larsen-toubro:2024:closing_cash:report2024` | 11958.50 | 533 | Cash and cash equivalents at end of the year [Note 14] |
| `larsen-toubro:2025:total_assets:report2025` | 379524.10 | 590 | TOTAL ASSETS |
| `larsen-toubro:2025:cash_and_cash_equivalents:report2025` | 12187.00 | 590 | Cash and cash equivalents |
| `larsen-toubro:2025:inventory:report2025` | 7670.55 | 590 | Inventories |
| `larsen-toubro:2025:current_receivables:report2025` | 53713.68 | 590 | Trade receivables |
| `larsen-toubro:2025:share_capital:report2025` | 275.04 | 591 | Equity share capital |
| `larsen-toubro:2025:other_equity:report2025` | 97380.56 | 591 | Other equity |
| `larsen-toubro:2025:total_equity_liabilities:report2025` | 379524.10 | 591 | TOTAL EQUITY AND LIABILITIES |
| `larsen-toubro:2025:noncurrent_assets:report2025` | 134182.39 | 590 | Sub-total - Non-current assets |
| `larsen-toubro:2025:current_assets:report2025` | 245184.27 | 590 | Sub-total - Current assets |
| `larsen-toubro:2025:total_equity:report2025` | 115403.68 | 591 | TOTAL EQUITY |
| `larsen-toubro:2025:total_liabilities:report2025` | 264120.42 | 591 | TOTAL LIABILITIES |
| `larsen-toubro:2025:current_liabilities:report2025` | 201970.90 | 591 | Sub-total - Current liabilities |
| `larsen-toubro:2025:noncurrent_liabilities:report2025` | 62149.52 | 591 | Sub-total - Non-current liabilities |
| `larsen-toubro:2025:lt_reported_revenue:report2025` | 255734.45 | 592 | Revenue from operations |
| `larsen-toubro:2025:other_income:report2025` | 4124.82 | 592 | Other income (net) |
| `larsen-toubro:2025:total_income:report2025` | 259859.27 | 592 | Total Income |
| `larsen-toubro:2025:lt_corporate_finance_costs:report2025` | 3334.37 | 592 | Finance costs |
| `larsen-toubro:2025:total_expenses:report2025` | 236755.26 | 592 | Total Expenses |
| `larsen-toubro:2025:profit_for_year:report2025` | 17673.33 | 592 | Profit for the period |
| `larsen-toubro:2025:cff:report2025` | 6556.62 | 597 | Net cash generated from/(used in) financing activities |
| `larsen-toubro:2025:closing_cash:report2025` | 12187.00 | 597 | Cash and cash equivalents at end of the year |
| `larsen-toubro:2026:total_assets:report2026` | 452549.88 | 616 | TOTAL ASSETS |
| `larsen-toubro:2026:cash_and_cash_equivalents:report2026` | 15391.24 | 616 | Cash and cash equivalents |
| `larsen-toubro:2026:inventory:report2026` | 9530.93 | 616 | Inventories |
| `larsen-toubro:2026:current_receivables:report2026` | 60461.26 | 616 | Trade receivables |
| `larsen-toubro:2026:share_capital:report2026` | 275.13 | 617 | Equity share capital |
| `larsen-toubro:2026:other_equity:report2026` | 109014.67 | 617 | Other equity |
| `larsen-toubro:2026:total_equity_liabilities:report2026` | 452549.88 | 617 | TOTAL EQUITY AND LIABILITIES |
| `larsen-toubro:2026:noncurrent_assets:report2026` | 134238.56 | 616 | Sub-total - Non-current assets |
| `larsen-toubro:2026:current_assets:report2026` | 292841.13 | 616 | Sub-total - Current assets |
| `larsen-toubro:2026:total_equity:report2026` | 128530.46 | 617 | TOTAL EQUITY |
| `larsen-toubro:2026:total_liabilities:report2026` | 324019.42 | 617 | TOTAL LIABILITIES |
| `larsen-toubro:2026:current_liabilities:report2026` | 233531.47 | 617 | Sub-total - Current liabilities |
| `larsen-toubro:2026:noncurrent_liabilities:report2026` | 69521.91 | 617 | Sub-total - Non-current liabilities |
| `larsen-toubro:2026:lt_reported_revenue:report2026` | 285874.36 | 618 | Revenue from operations |
| `larsen-toubro:2026:other_income:report2026` | 5760.68 | 618 | Other income (net) |
| `larsen-toubro:2026:total_income:report2026` | 291635.04 | 618 | Total Income |
| `larsen-toubro:2026:lt_corporate_finance_costs:report2026` | 2848.82 | 618 | Finance costs |
| `larsen-toubro:2026:total_expenses:report2026` | 263936.79 | 618 | Total Expenses |
| `larsen-toubro:2026:profit_for_year:report2026` | 18953.88 | 618 | Profit for the year |
| `larsen-toubro:2026:cfo:report2026` | 16740.97 | 622 | Net cash generated from operating activities |
| `larsen-toubro:2026:cfi:report2026` | (11738.84) | 622 | Net cash used in investing activities |
| `larsen-toubro:2026:cff:report2026` | (2156.43) | 623 | Net cash generated from/(used in) financing activities |
| `larsen-toubro:2026:closing_cash:report2026` | 15391.24 | 623 | Cash and cash equivalents at end of the year |

## tata-motors: 63 candidate facts

| Exact observation ID | Printed INR crore | PDF page | Printed label |
|---|---:|---:|---|
| `tata-motors:2022:total_assets:report2022` | 330,619.93 | 290 | TOTAL ASSETS |
| `tata-motors:2022:cash_and_cash_equivalents:report2022` | 38,159.01 | 290 | Cash and cash equivalents |
| `tata-motors:2022:inventory:report2022` | 35,240.34 | 290 | Inventories |
| `tata-motors:2022:current_receivables:report2022` | 12,442.12 | 290 | Trade receivables |
| `tata-motors:2022:share_capital:report2022` | 765.88 | 290 | Equity share capital |
| `tata-motors:2022:other_equity:report2022` | 43,795.36 | 290 | Other equity |
| `tata-motors:2022:total_equity_liabilities:report2022` | 330,619.93 | 290 | TOTAL EQUITY AND LIABILITIES |
| `tata-motors:2022:tata_reported_revenue:report2022` | 278,453.62 | 291 | Total revenue from operations |
| `tata-motors:2022:other_income:report2022` | 3,053.63 | 291 | Other income (includes government incentives) |
| `tata-motors:2022:total_income:report2022` | 281,507.25 | 291 | III. Total Income (I+II) |
| `tata-motors:2022:finance_costs:report2022` | 9,311.86 | 291 | Finance costs |
| `tata-motors:2022:total_expenses:report2022` | 287,881.08 | 291 | Total Expenses (IV) |
| `tata-motors:2022:profit_for_year:report2022` | (11,308.76) | 291 | XI. Profit/(loss) for the year (IX+X) |
| `tata-motors:2022:cfo:report2022` | 14,282.83 | 292 | Net cash from operating activities |
| `tata-motors:2022:cfi:report2022` | (4,775.12) | 293 | Net cash used in investing activities |
| `tata-motors:2022:cff:report2022` | (3,380.17) | 293 | Net cash (used in)/from financing activities |
| `tata-motors:2022:closing_cash:report2022` | 38,159.01 | 293 | Cash and cash equivalents as at March 31, (closing balance) |
| `tata-motors:2023:total_assets:report2023` | 336,081.38 | 356 | TOTAL ASSETS |
| `tata-motors:2023:cash_and_cash_equivalents:report2023` | 31,886.95 | 356 | Cash and cash equivalents |
| `tata-motors:2023:inventory:report2023` | 40,755.39 | 356 | Inventories |
| `tata-motors:2023:current_receivables:report2023` | 15,737.97 | 356 | Trade receivables |
| `tata-motors:2023:share_capital:report2023` | 766.02 | 356 | Equity share capital |
| `tata-motors:2023:other_equity:report2023` | 44,555.77 | 356 | Other equity |
| `tata-motors:2023:total_equity_liabilities:report2023` | 336,081.38 | 356 | TOTAL EQUITY AND LIABILITIES |
| `tata-motors:2023:tata_reported_revenue:report2023` | 345,966.97 | 357 | Total revenue from operations |
| `tata-motors:2023:other_income:report2023` | 4,633.18 | 357 | Other income (includes government incentives) |
| `tata-motors:2023:total_income:report2023` | 350,600.15 | 357 | Total Income (I+II) |
| `tata-motors:2023:finance_costs:report2023` | 10,225.48 | 357 | Finance costs |
| `tata-motors:2023:total_expenses:report2023` | 349,133.13 | 357 | Total Expenses (IV) |
| `tata-motors:2023:profit_for_year:report2023` | 2,689.87 | 357 | Profit/(loss) for the year (IX+X) |
| `tata-motors:2023:cfo:report2023` | 35,388.01 | 358 | Net cash from operating activities |
| `tata-motors:2023:cfi:report2023` | (16,804.16) | 359 | Net cash used in investing activities |
| `tata-motors:2023:cff:report2023` | (26,242.90) | 359 | Net cash (used in)/from financing activities |
| `tata-motors:2023:closing_cash:report2023` | 31,886.95 | 359 | Cash and cash equivalents as at March 31, (closing balance) |
| `tata-motors:2025:total_assets:report2025` | 3,78,642 | 313 | TOTAL ASSETS |
| `tata-motors:2025:cash_and_cash_equivalents:report2025` | 34,349 | 313 | Cash and cash equivalents |
| `tata-motors:2025:inventory:report2025` | 47,269 | 313 | Inventories |
| `tata-motors:2025:current_receivables:report2025` | 13,248 | 313 | Trade receivables |
| `tata-motors:2025:share_capital:report2025` | 736 | 313 | Equity share capital |
| `tata-motors:2025:other_equity:report2025` | 1,15,408 | 313 | Other equity |
| `tata-motors:2025:total_equity_liabilities:report2025` | 3,78,642 | 313 | TOTAL EQUITY AND LIABILITIES |
| `tata-motors:2025:profit_for_year:report2025` | 28,149 | 314 | Profit for the year (XI+XIV) |
| `tata-motors:2025:cfo:report2025` | 63,102 | 316 | Net cash from operating activities |
| `tata-motors:2025:cfi:report2025` | (47,594) | 317 | Net cash used in investing activities |
| `tata-motors:2025:cff:report2025` | (18,786) | 317 | Net cash used in financing activities |
| `tata-motors:2025:closing_cash:report2025` | 34,349 | 317 | Cash and cash equivalents as at March 31, (closing balance) |
| `tata-motors:2026:total_assets:report2026` | 381,922 | 331 | TOTAL ASSETS |
| `tata-motors:2026:cash_and_cash_equivalents:report2026` | 22,880 | 331 | Cash and cash equivalents |
| `tata-motors:2026:inventory:report2026` | 50,126 | 331 | Inventories |
| `tata-motors:2026:current_receivables:report2026` | 12,619 | 331 | Trade receivables |
| `tata-motors:2026:share_capital:report2026` | 737 | 331 | Equity share capital |
| `tata-motors:2026:other_equity:report2026` | 111,331 | 331 | Other equity |
| `tata-motors:2026:total_equity_liabilities:report2026` | 381,922 | 331 | TOTAL EQUITY AND LIABILITIES |
| `tata-motors:2026:tata_reported_revenue:report2026` | 335,582 | 332 | Total revenue from operations |
| `tata-motors:2026:other_income:report2026` | 5,787 | 332 | Other income |
| `tata-motors:2026:total_income:report2026` | 341,369 | 332 | Total income (I+II) |
| `tata-motors:2026:finance_costs:report2026` | 2,827 | 332 | Finance costs |
| `tata-motors:2026:total_expenses:report2026` | 339,296 | 332 | Total expenses (IV) |
| `tata-motors:2026:profit_for_year:report2026` | 82,645 | 332 | Profit for the year (XI+XV) |
| `tata-motors:2026:cfo:report2026` | 13,041 | 334 | Net cash from operating activities |
| `tata-motors:2026:cfi:report2026` | (24,810) | 335 | Net cash used in investing activities |
| `tata-motors:2026:cff:report2026` | (1,344) | 335 | Net cash used in financing activities |
| `tata-motors:2026:closing_cash:report2026` | 22,880 | 335 | Cash and cash equivalents as at March 31, (closing balance) |

## Withheld conflicts

The [conflict ledger](conflict_ledger.json) records all 40 keys, their original/current and comparative values, dated columns, source hashes and pages. All remain outside the candidate CSV and pending plan. A later report does not silently replace an original report. Conflicts arising from HDFC amalgamation, L&T reporting changes and Tata re-presented operations are not automatically classified as source errors.

## Exact approval boundary

If accepted, record actual source and candidate decisions under this catalog in a private ledger, with reviewer, UTC timestamp and substantive rationale. Explicitly accept the Tata original-entity continuity proposal and reported-scope definitions. Approve only the exact 255 IDs in `review_index.json` and the 15 listed source keys; retain all 40 conflict keys withheld. This is separate from Marky’s 56-fact RIL/TCS approval. The RIL/TCS 318-fact BS/CF packet is a separate catalog and ledger.

Fresh privileged snapshots must cover these three companies. Regenerate plans after real decisions; inspect plan and live schema hashes, preview the atomic publisher, then explicitly apply. Retain receipts and verify all production facts/provenance. A pending offline plan is not an executable or native load preview.
