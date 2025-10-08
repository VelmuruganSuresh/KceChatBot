require("dotenv").config();
const { Storage } = require("@google-cloud/storage");

const storage = new Storage({
  keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS,
});

async function listBuckets() {
  const [buckets] = await storage.getBuckets();
  console.log("Buckets:", buckets);
}

listBuckets();
