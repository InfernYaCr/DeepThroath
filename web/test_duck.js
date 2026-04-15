const { DuckDBInstance } = require('@duckdb/node-api');
async function run() {
  const instance = await DuckDBInstance.create(':memory:');
  const conn = await instance.connect();
  const res = await conn.run("SELECT * FROM read_parquet('../results/latest.parquet') LIMIT 1");
  const rows = await res.getRows();
  console.log(rows[0]);
  console.log(rows[0].toJSON());
}
run().catch(console.error);
