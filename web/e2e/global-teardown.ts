import { execFile } from "node:child_process";
import { promisify } from "node:util";

const run = promisify(execFile);

/** E2E 가 만든 계정을 지운다. 테스트 시 생성 이후 삭제 */
export default async function globalTeardown() {
  try {
    const { stdout } = await run(
      process.platform === "win32" ? "uv.exe" : "uv",
      ["run", "python", "-m", "scripts.cleanup_test_users", "--apply"],
      { cwd: "../backend" },
    );
    process.stdout.write(`\n[teardown] ${stdout.trim()}\n`);
  } catch (e) {
    // 다음 실행에서 같이 지워진다
    process.stdout.write(`\n[teardown] 계정 정리 실패: ${e}\n`);
  }
}
