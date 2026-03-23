import fs from "node:fs";
import path from "node:path";

const OPERATOR_UI_ROOT = path.resolve(__dirname, "..", "..");
const GUARDED_DIRECTORIES = [
  path.join(OPERATOR_UI_ROOT, "app"),
  path.join(OPERATOR_UI_ROOT, "components"),
];
const INLINE_STYLE_PATTERN = /\bstyle\s*=\s*\{\{/;
const SOURCE_FILE_PATTERN = /\.(ts|tsx)$/i;
const TEST_FILE_PATTERN = /\.test\.(ts|tsx)$/i;

// Add an entry only when inline style is unavoidable, with a short reason.
const ALLOWED_INLINE_STYLE_EXCEPTIONS: Record<string, string> = {};

function toPosixRelativePath(absolutePath: string): string {
  return path.relative(OPERATOR_UI_ROOT, absolutePath).split(path.sep).join("/");
}

function collectSourceFiles(directoryPath: string): string[] {
  const entries = fs.readdirSync(directoryPath, { withFileTypes: true });
  const sourceFiles: string[] = [];

  for (const entry of entries) {
    const fullPath = path.join(directoryPath, entry.name);
    if (entry.isDirectory()) {
      sourceFiles.push(...collectSourceFiles(fullPath));
      continue;
    }

    if (!SOURCE_FILE_PATTERN.test(entry.name) || TEST_FILE_PATTERN.test(entry.name)) {
      continue;
    }

    sourceFiles.push(fullPath);
  }

  return sourceFiles;
}

describe("layout guardrails", () => {
  it("does not allow inline style props in app/components source", () => {
    const violations: string[] = [];

    for (const guardedDirectory of GUARDED_DIRECTORIES) {
      for (const sourceFile of collectSourceFiles(guardedDirectory)) {
        const relativePath = toPosixRelativePath(sourceFile);
        if (ALLOWED_INLINE_STYLE_EXCEPTIONS[relativePath]) {
          continue;
        }

        const fileContents = fs.readFileSync(sourceFile, "utf8");
        if (INLINE_STYLE_PATTERN.test(fileContents)) {
          violations.push(relativePath);
        }
      }
    }

    if (violations.length > 0) {
      throw new Error(
        [
          "Inline style regression detected in operator UI source files:",
          ...violations.map((item) => `- ${item}`),
          "Use shared layout primitives/classes instead (PageContainer, SectionCard, row-wrap, metrics-grid, table-container).",
          "If a true exception is unavoidable, document it in ALLOWED_INLINE_STYLE_EXCEPTIONS with a reason.",
        ].join("\n"),
      );
    }
  });
});
