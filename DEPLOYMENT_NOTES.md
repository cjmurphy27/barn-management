# Deployment Notes

## Railway Database Setup

### Initial Production Database Migrations (COMPLETED ✅)

The following database migrations were applied to Railway production on 2025-08-31:

```sql
-- Allow NULL values for delivery receipts without pricing
ALTER TABLE transactions ALTER COLUMN total_amount DROP NOT NULL;
ALTER TABLE transaction_items ALTER COLUMN total_cost DROP NOT NULL;
```

**Why needed:** Delivery receipts and packing slips often don't have pricing information, but we still want to track the items received.

**Status:** ✅ Completed - no further action needed

### Future Deployments

Regular deployments only require:
1. `git add .`
2. `git commit -m "Description of changes"`
3. `git push origin main`
4. Railway auto-deploys from GitHub

### Database Connection Info

Railway PostgreSQL can be accessed via the Railway dashboard:
- Project → PostgreSQL service → Data → Connect
- Connection string format: `postgresql://postgres:PASSWORD@HOST:PORT/railway`

### Key Features in Production

✅ AI-powered receipt scanner for delivery receipts  
✅ Automatic inventory item extraction and addition  
✅ Transaction viewing with editing capabilities  
✅ Support for documents without pricing (delivery receipts, packing slips)  
✅ Duplicate prevention and error handling  