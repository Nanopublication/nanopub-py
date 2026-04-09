let config = require("semantic-release-preconfigured-conventional-commits")
config.branches = ["release"]
config.plugins.push(
  [
    "@semantic-release/exec",
    {
      "prepareCmd": `uv version \${nextRelease.version} && uv build`,
      "publishCmd": "uv publish"
    }
  ],
  "@semantic-release/github",
  [
    "@semantic-release/git",
    {
      "assets": ["pyproject.toml", "CHANGELOG.md", "uv.lock"]
    }
  ]
)
module.exports = config
