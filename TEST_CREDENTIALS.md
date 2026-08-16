# 📑 ATM Simulation — Test Credentials & Presentation Guide

> [!TIP]
> **For Live College Presentation**: Use the **Curated Quick Demo Scenarios** below. You only need 1 or 2 accounts to demonstrate every feature (Withdrawals, Deposits, Security Lockouts, and Admin Unlocking).

---

## 🎯 1. Curated Quick Demo Scenarios

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

## 🔑 2. General Customer Account PIN Directory (`10003` – `10020`)

*(Accounts `10001` and `10002` are featured at the top in Section 1)*

| Account # | PIN | Account # | PIN | Account # | PIN |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **`10003`** | `9999` | **`10009`** | `5555` | **`10015`** | `3434` |
| **`10004`** | `0000` | **`10010`** | `6666` | **`10016`** | `4545` |
| **`10005`** | `1111` | **`10011`** | `7777` | **`10017`** | `5656` |
| **`10006`** | `2222` | **`10012`** | `8888` | **`10018`** | `6767` |
| **`10007`** | `3333` | **`10013`** | `1212` | **`10019`** | `7878` |
| **`10008`** | `4444` | **`10014`** | `2323` | **`10020`** | `8989` |

---

## 👑 3. VIP & Institutional Reserve Directory (`10021` – `10100`)

> [!NOTE]
> High-net-worth accounts pre-seeded in the database for presentation and liquidity management.

| Account # | PIN | Account # | PIN | Account # | PIN | Account # | PIN |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`10021`** | `4545` | **`10041`** | `1010` | **`10061`** | `8989` | **`10081`** | `6464` |
| **`10022`** | `1818` | **`10042`** | `1212` | **`10062`** | `1212` | **`10082`** | `0909` |
| **`10023`** | `0707` | **`10043`** | `4444` | **`10063`** | `2929` | **`10083`** | `9999` |
| **`10024`** | `1010` | **`10044`** | `0505` | **`10064`** | `1919` | **`10084`** | `2525` |
| **`10025`** | `3333` | **`10045`** | `0303` | **`10065`** | `1111` | **`10085`** | `1616` |
| **`10026`** | `9393` | **`10046`** | `3434` | **`10066`** | `1515` | **`10086`** | `9797` |
| **`10027`** | `7777` | **`10047`** | `1010` | **`10067`** | `2323` | **`10087`** | `3737` |
| **`10028`** | `0101` | **`10048`** | `2810` | **`10068`** | `0303` | **`10088`** | `3131` |
| **`10029`** | `1717` | **`10049`** | `0808` | **`10069`** | `2020` | **`10089`** | `2323` |
| **`10030`** | `1414` | **`10050`** | `1919` | **`10070`** | `0505` | **`10090`** | `0404` |
| **`10031`** | `0808` | **`10051`** | `1983` | **`10071`** | `5454` | **`10091`** | `2727` |
| **`10032`** | `1818` | **`10052`** | `1000` | **`10072`** | `9090` | **`10092`** | `1567` |
| **`10033`** | `8484` | **`10053`** | `1985` | **`10073`** | `7373` | **`10093`** | `2222` |
| **`10034`** | `0303` | **`10054`** | `1111` | **`10074`** | `2424` | **`10094`** | `8484` |
| **`10035`** | `2525` | **`10055`** | `2222` | **`10075`** | `0202` | **`10095`** | `0202` |
| **`10036`** | `0606` | **`10056`** | `3333` | **`10076`** | `1500` | **`10096`** | `1818` |
| **`10037`** | `0505` | **`10057`** | `4444` | **`10077`** | `6565` | **`10097`** | `0101` |
| **`10038`** | `2828` | **`10058`** | `6464` | **`10078`** | `4949` | **`10098`** | `3535` |
| **`10039`** | `1313` | **`10059`** | `5656` | **`10079`** | `5656` | **`10099`** | `9292` |
| **`10040`** | `0909` | **`10060`** | `7878` | **`10080`** | `3535` | **`10100`** | `1111` |

---

## 🔒 Security Compliance Note

> [!NOTE]
> All PINs are stored in `atm.db` using **PBKDF2-HMAC-SHA256 (100,000 iterations)** with unique 16-byte random salts and server-side secret peppers. Plaintext PINs are never stored or logged in the database.
