import { buildApp } from "./app.js";

const app = buildApp();

const port = Number(process.env.PORT ?? 4000);
const host = "0.0.0.0";

app
  .listen({ port, host })
  .then(() => {
    app.log.info(`Work Boots Console API listening on http://${host}:${port}`);
  })
  .catch((error) => {
    app.log.error(error);
    process.exit(1);
  });
