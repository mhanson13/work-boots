import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().default(4000),
  DATABASE_URL: z.string().min(1),
  USE_MOCK_INTEGRATIONS: z
    .string()
    .default("true")
    .transform((value) => value.toLowerCase() === "true"),
  GOOGLE_SERVICE_ACCOUNT_JSON: z.string().optional(),
  GBP_LOCATION_ID: z.string().optional(),
  GA4_PROPERTY_ID: z.string().optional(),
  SEARCH_CONSOLE_SITE_URL: z.string().optional()
});

export type Env = z.infer<typeof envSchema>;

export function loadEnv(input: NodeJS.ProcessEnv = process.env): Env {
  return envSchema.parse(input);
}
