# Roadmap

BrightLoop is an early prototype. This roadmap describes intended work, not
features that already exist.

## 0.1 — Safe local prototype
- [x] Claude-generated structured plans
- [x] Preview before applying
- [x] Explicit approval before local changes
- [x] Markdown note creation and daily-log append
- [x] Input validation and unit tests

## Next milestones
- [ ] More tests, including mocked Claude responses and malformed model output
- [ ] A provider interface so users can select a supported model
- [ ] Optional, narrowly scoped integrations (for example, calendar task export)
- [ ] Scheduled workflows with a visible run history
- [ ] A small web interface for non-technical users
- [ ] Documentation, accessibility improvements, and community feedback

Any future integration should use least-privilege permissions, clear previews,
and explicit approval for actions with external effects.
