# StockWise Inventory Management System

## Updated access rules
- Admin: add records; update/delete products (existing product edit/delete routes are protected server-side).
- User: add and view products, categories, suppliers, customers, purchases and sales.
- Both roles can view reports.
- Purchase entries increase product stock; sales entries reduce stock and reject sales above available stock.

## Run
1. Set your local MySQL password in `db_connection.py`.
2. Ensure the database and tables in `database/schema.sql` exist. Do not rerun schema creation if your tables already contain data; the script uses `CREATE TABLE IF NOT EXISTS`.
3. Install: `py -m pip install -r requirements.txt`
4. Start: `py main.py`
5. Open: `http://127.0.0.1:5000/welcome`

Public registration always creates a `user` account. Promote an account to admin using your MySQL client only if needed: `UPDATE App_User SET Role='admin' WHERE Username='your_username';`

Note: This update enables user additions and adds a role-selection landing page. Existing admin-only update/delete controls are currently implemented for products; the other master-data pages currently support add/view.
