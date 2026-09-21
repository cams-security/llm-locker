class LlmLocker < Formula
  desc "MCP client for llm-locker — end-to-end encrypted memory for LLMs"
  homepage "https://github.com/cams-security/llm-locker"
  url "https://github.com/cams-security/llm-locker.git", branch: "main"
  version "1.0.0"
  license "MIT"

  depends_on "node"

  def install
    cd "mcp-server-node" do
      # Local install first (with devDependencies, e.g. typescript) so we
      # can run the build — Homebrew's std_npm_args below passes
      # --ignore-scripts, which deliberately skips lifecycle scripts like
      # our "build", so it has to happen explicitly and separately.
      system "npm", "install"
      system "npm", "run", "build"
      # Now the Homebrew-blessed global-style install into libexec, now
      # that dist/ actually exists to be copied along with the rest.
      system "npm", "install", *std_npm_args
      bin.install_symlink libexec.glob("bin/*")
    end
  end

  test do
    # No real LOCKER_API_KEY/LOCKER_ENCRYPTION_KEY in a test environment —
    # confirm it fails loudly with the expected message rather than
    # silently, which is itself the behavior worth testing.
    output = shell_output("#{bin}/llm-locker-mcp 2>&1", 1)
    assert_match "LOCKER_API_KEY", output
  end
end
