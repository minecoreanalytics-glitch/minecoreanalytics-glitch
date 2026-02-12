# Testing BigQuery Connection

If you are experiencing issues connecting to BigQuery, follow these steps to diagnose the problem.

## 1. Run the Debug Script

We have provided a standalone script to verify your credentials and schema outside of the main application.

1. Open your terminal.
2. Navigate to the project root.
3. Run the script:
   ```bash
   python3 backend/scripts/debug_bq_connection.py
   ```

## 2. Provide Credentials

The script will ask for your credentials. You can either:

* Paste the **absolute path** to your Service Account JSON file (e.g., `/Users/me/keys/my-sa.json`).
* Paste the **JSON content** directly into the terminal.

## 3. Interpret Results

### Connection Failed

If the script says `❌ Connection Failed`, check:

* **Credentials:** Is the JSON file valid? Has the key expired?
* **Permissions:** Does the Service Account have `BigQuery Job User` and `BigQuery Data Viewer` roles?
* **API Enabled:** Is the BigQuery API enabled in your Google Cloud Console?

### Missing Tables

If the script says `❌ Table 'customers' NOT found`, your application will not work correctly.

* **Action:** You must create the required tables (`customers`, `invoices`, `interactions`) in your BigQuery dataset.
* **Schema:** Refer to `backend/core/config/htv_config.yaml` for the expected fields.

## 4. Application Configuration

Once the script passes, ensure your application is using the correct Project ID and Dataset.

* Edit `backend/core/config/htv_config.yaml`
* Update `project_id` and `dataset` under the `bigquery` section.
