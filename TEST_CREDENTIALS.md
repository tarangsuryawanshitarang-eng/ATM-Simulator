# 📑 ATM Simulation — Test Credentials & Presentation Guide

> [!TIP]
> **For Live College Presentation**: Use the **Curated Quick Demo Scenarios** below. You only need 1 or 2 accounts to demonstrate every feature (Withdrawals, Deposits, Security Lockouts, and Admin Unlocking).

---

## 🎯 1. Curated Quick Demo Scenarios

Use these pre-configured accounts during your presentation for specific demo flows:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  DEMO CASE 1: Lead Developer Account (Primary Presentation Account)                    │
│  • Account Number : 10001                                                              │
│  • Account Holder : Tarang Suryawanshi (Lead Developer)                                │
│  • Security PIN   : 1234                                                               │
│  • Balance        : $2,500.00 (Status: 🟢 ACTIVE)                                      │
│  • Best For       : Standard Cash Withdrawal, Masked PIN, & Thermal Receipts           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  DEMO CASE 2: Project Partner Account                                                  │
│  • Account Number : 10002                                                              │
│  • Account Holder : Sameep Patel (Project Partner)                                     │
│  • Security PIN   : 4321                                                               │
│  • Balance        : $1,000.00 (Status: 🟢 ACTIVE)                                      │
│  • Best For       : Cash Deposit flow & Mini-Statement verification                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  DEMO CASE 3: Security Lockout & Admin Unlock Protocol                                 │
│  • Account Number : 10004                                                              │
│  • Account Holder : Aditya Verma                                                       │
│  • Security PIN   : 0000                                                               │
│  • Balance        : $300.00 (Status: 🔴 LOCKED - 3 Failed Attempts)                    │
│  • Best For       : Login in main.py to show lockout alert, then unlock via admin.py   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  DEMO CASE 4: Edge Case — Insufficient Funds Rejection                                 │
│  • Account Number : 10003                                                              │
│  • Account Holder : Diya Iyer                                                          │
│  • Security PIN   : 9999                                                               │
│  • Balance        : $50.00 (Status: 🟢 ACTIVE)                                         │
│  • Best For       : Attempting a $200 withdrawal to demonstrate clean overdraft denial │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  DEMO CASE 5: High-Net-Worth VIP Customer                                              │
│  • Account Number : 10022                                                              │
│  • Account Holder : Virat Kohli                                                        │
│  • Security PIN   : 1818                                                               │
│  • Balance        : $50,000.00 (Status: 🟢 ACTIVE)                                     │
│  • Best For       : Multi-denomination $2,000 withdrawal (500x4 notes)                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 👥 2. Full Account Directory (Segmented by Tier)

### 🔹 Tier 1: Core Customer Profiles (`10001` – `10025`)

| Account # | Account Holder | PIN | Balance ($) | Status | Suggested Use Case |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **`10001`** | **Tarang Suryawanshi** | `1234` | `$2,500.00` | 🟢 Active | **Lead Developer / Primary Demo** |
| **`10002`** | **Sameep Patel** | `4321` | `$1,000.00` | 🟢 Active | **Project Partner / Fast Cash** |
| **`10003`** | Diya Iyer | `9999` | `$50.00` | 🟢 Active | Low Balance / Insufficient Funds |
| **`10004`** | Aditya Verma | `0000` | `$300.00` | 🔴 **Locked** | Lockout & Manager Unlock Demo |
| **`10005`** | Aarav Sharma | `1111` | `$5,000.00` | 🟢 Active | Cash Deposit Demonstration |
| **`10006`** | Vivaan Patel | `2222` | `$7,500.00` | 🟢 Active | High Balance Transactions |
| **`10007`** | Ananya Gupta | `3333` | `$12,000.00` | 🟢 Active | General Banking |
| **`10008`** | Rahul Deshmukh | `4444` | `$3,200.00` | 🟢 Active | Mini-Statement & PIN Change |
| **`10009`** | Sneha Joshi | `5555` | `$1,500.00` | 🟢 Active | Standard Withdrawal |
| **`10010`** | Priya Nair | `6666` | `$8,900.00` | 🟢 Active | General Banking |
| **`10011`** | Rohan Mehta | `7777` | `$4,500.00` | 🟢 Active | Standard Deposit |
| **`10012`** | Vikram Singh | `8888` | `$6,200.00` | 🟢 Active | Fast Cash |
| **`10013`** | Pooja Reddy | `1212` | `$2,100.00` | 🟢 Active | General Banking |
| **`10014`** | Neha Kulkarni | `2323` | `$9,400.00` | 🟢 Active | General Banking |
| **`10015`** | Arjun Rao | `3434` | `$11,000.00` | 🟢 Active | Large Withdrawal |
| **`10016`** | Rajesh Kumar | `4545` | `$5,300.00` | 🟢 Active | Standard Transactions |
| **`10017`** | Sunita Devi | `5656` | `$1,800.00` | 🟢 Active | Standard Deposit |
| **`10018`** | Amit Shah | `6767` | `$14,500.00` | 🟢 Active | High Liquidity |
| **`10019`** | Kavita Menon | `7878` | `$3,700.00` | 🟢 Active | General Banking |
| **`10020`** | Suresh Raina | `8989` | `$16,000.00` | 🟢 Active | VIP Banking |
| **`10021`** | Rohit Sharma | `4545` | `$25,000.00` | 🟢 Active | High Volume Dispense |
| **`10022`** | Virat Kohli | `1818` | `$50,000.00` | 🟢 Active | Maximum Liquidity |
| **`10023`** | MS Dhoni | `0707` | `$45,000.00` | 🟢 Active | VIP Customer |
| **`10024`** | Sachin Tendulkar | `1010` | `$35,000.00` | 🟢 Active | VIP Customer |
| **`10025`** | Hardik Pandya | `3333` | `$22,000.00` | 🟢 Active | Fast Cash |

---

### 🔹 Tier 2: VIP & Sports Profiles (`10026` – `10050`)

| Account # | Account Holder | PIN | Balance ($) | Status | Account # | Account Holder | PIN | Balance ($) | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: |
| **`10026`** | Jasprit Bumrah | `9393` | `$28,000.00` | 🟢 Active | **`10039`** | Richa Ghosh | `1313` | `$11,500.00` | 🟢 Active |
| **`10027`** | Shubman Gill | `7777` | `$19,000.00` | 🟢 Active | **`10040`** | Pooja Vastrakar | `0909` | `$12,500.00` | 🟢 Active |
| **`10028`** | KL Rahul | `0101` | `$24,000.00` | 🟢 Active | **`10041`** | Renuka Singh | `1010` | `$13,500.00` | 🟢 Active |
| **`10029`** | Rishabh Pant | `1717` | `$21,000.00` | 🟢 Active | **`10042`** | Yuvraj Singh | `1212` | `$34,000.00` | 🟢 Active |
| **`10030`** | Sanju Samson | `1414` | `$13,000.00` | 🟢 Active | **`10043`** | Virender Sehwag | `4444` | `$32,000.00` | 🟢 Active |
| **`10031`** | Ravindra Jadeja | `0808` | `$31,000.00` | 🟢 Active | **`10044`** | Gautam Gambhir | `0505` | `$29,000.00` | 🟢 Active |
| **`10032`** | Smriti Mandhana | `1818` | `$27,000.00` | 🟢 Active | **`10045`** | Harbhajan Singh | `0303` | `$27,500.00` | 🟢 Active |
| **`10033`** | Harmanpreet Kaur | `8484` | `$23,000.00` | 🟢 Active | **`10046`** | Zaheer Khan | `3434` | `$26,500.00` | 🟢 Active |
| **`10034`** | Mithali Raj | `0303` | `$30,000.00` | 🟢 Active | **`10047`** | Anil Kumble | `1010` | `$38,000.00` | 🟢 Active |
| **`10035`** | Jhulan Goswami | `2525` | `$26,000.00` | 🟢 Active | **`10048`** | VVS Laxman | `2810` | `$33,000.00` | 🟢 Active |
| **`10036`** | Deepti Sharma | `0606` | `$14,000.00` | 🟢 Active | **`10049`** | Sourav Ganguly | `0808` | `$41,000.00` | 🟢 Active |
| **`10037`** | Jemimah Rodrigues | `0505` | `$15,500.00` | 🟢 Active | **`10050`** | Rahul Dravid | `1919` | `$42,000.00` | 🟢 Active |
| **`10038`** | Shafali Verma | `2828` | `$16,500.00` | 🟢 Active | | | | | |

---

### 🔹 Tier 3: Legends & Veteran Profiles (`10051` – `10075`)

| Account # | Account Holder | PIN | Balance ($) | Status | Account # | Account Holder | PIN | Balance ($) | Status |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| **`10051`** | Kapil Dev | `1983` | `$48,000.00` | 🟢 Active | **`10064`** | Umesh Yadav | `1919` | `$24,000.00` | 🟢 Active |
| **`10052`** | Sunil Gavaskar | `1000` | `$46,000.00` | 🟢 Active | **`10065`** | Mohammed Shami | `1111` | `$29,500.00` | 🟢 Active |
| **`10053`** | Ravi Shastri | `1985` | `$36,000.00` | 🟢 Active | **`10066`** | Bhuvneshwar Kumar | `1515` | `$26,000.00` | 🟢 Active |
| **`10054`** | Dilip Vengsarkar | `1111` | `$20,000.00` | 🟢 Active | **`10067`** | Kuldeep Yadav | `2323` | `$21,000.00` | 🟢 Active |
| **`10055`** | Chetan Sharma | `2222` | `$18,500.00` | 🟢 Active | **`10068`** | Yuzvendra Chahal | `0303` | `$22,000.00` | 🟢 Active |
| **`10056`** | Javagal Srinath | `3333` | `$22,500.00` | 🟢 Active | **`10069`** | Axar Patel | `2020` | `$23,000.00` | 🟢 Active |
| **`10057`** | Venkatesh Prasad | `4444` | `$21,500.00` | 🟢 Active | **`10070`** | Washington Sundar | `0505` | `$19,000.00` | 🟢 Active |
| **`10058`** | Ashish Nehra | `6464` | `$24,500.00` | 🟢 Active | **`10071`** | Shardul Thakur | `5454` | `$18,000.00` | 🟢 Active |
| **`10059`** | Irfan Pathan | `5656` | `$23,500.00` | 🟢 Active | **`10072`** | Deepak Chahar | `9090` | `$17,000.00` | 🟢 Active |
| **`10060`** | Munaf Patel | `7878` | `$17,500.00` | 🟢 Active | **`10073`** | Mohammed Siraj | `7373` | `$25,000.00` | 🟢 Active |
| **`10061`** | RP Singh | `8989` | `$19,500.00` | 🟢 Active | **`10074`** | Prasidh Krishna | `2424` | `$16,000.00` | 🟢 Active |
| **`10062`** | Praveen Kumar | `1212` | `$16,500.00` | 🟢 Active | **`10075`** | Arshdeep Singh | `0202` | `$20,000.00` | 🟢 Active |
| **`10063`** | Ishant Sharma | `2929` | `$25,500.00` | 🟢 Active | | | | | |

---

### 🔹 Tier 4: Next-Gen Talent Profiles (`10076` – `10100`)

| Account # | Account Holder | PIN | Balance ($) | Status | Account # | Account Holder | PIN | Balance ($) | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: |
| **`10076`** | Umran Malik | `1500` | `$15,000.00` | 🟢 Active | **`10089`** | Sai Sudharsan | `2323` | `$17,500.00` | 🟢 Active |
| **`10077`** | Avesh Khan | `6565` | `$14,000.00` | 🟢 Active | **`10090`** | Abhishek Sharma | `0404` | `$23,500.00` | 🟢 Active |
| **`10078`** | Mukesh Kumar | `4949` | `$13,000.00` | 🟢 Active | **`10091`** | Nitish Kumar Reddy | `2727` | `$15,500.00` | 🟢 Active |
| **`10079`** | Ravi Bishnoi | `5656` | `$18,000.00` | 🟢 Active | **`10092`** | Mayank Yadav | `1567` | `$14,500.00` | 🟢 Active |
| **`10080`** | Rinku Singh | `3535` | `$22,000.00` | 🟢 Active | **`10093`** | Harshit Rana | `2222` | `$13,500.00` | 🟢 Active |
| **`10081`** | Yashasvi Jaiswal | `6464` | `$26,000.00` | 🟢 Active | **`10094`** | Prabhsimran Singh | `8484` | `$12,500.00` | 🟢 Active |
| **`10082`** | Tilak Varma | `0909` | `$19,000.00` | 🟢 Active | **`10095`** | Ayush Badoni | `0202` | `$11,500.00` | 🟢 Active |
| **`10083`** | Jitesh Sharma | `9999` | `$15,000.00` | 🟢 Active | **`10096`** | Nehal Wadhera | `1818` | `$10,500.00` | 🟢 Active |
| **`10084`** | Shivam Dube | `2525` | `$21,000.00` | 🟢 Active | **`10097`** | Abdul Samad | `0101` | `$12,000.00` | 🟢 Active |
| **`10085`** | Dhruv Jurel | `1616` | `$17,000.00` | 🟢 Active | **`10098`** | Shahrukh Khan | `3535` | `$16,000.00` | 🟢 Active |
| **`10086`** | Sarfaraz Khan | `9797` | `$18,500.00` | 🟢 Active | **`10099`** | Rahul Tewatia | `9292` | `$19,500.00` | 🟢 Active |
| **`10087`** | Devdutt Padikkal | `3737` | `$16,500.00` | 🟢 Active | **`10100`** | Sai Kishore | `1111` | `$14,000.00` | 🟢 Active |
| **`10088`** | Ruturaj Gaikwad | `3131` | `$24,000.00` | 🟢 Active | | | | | |

---

## 🔒 Security Compliance Note

> [!NOTE]
> All PINs are stored in `atm.db` using **PBKDF2-HMAC-SHA256 (100,000 iterations)** with unique 16-byte random salts and server-side secret peppers. Plaintext PINs are never stored or logged in the database.
