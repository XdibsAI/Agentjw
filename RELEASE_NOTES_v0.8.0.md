
## ⚠️ Known Issues (v0.8.0)

1. **Permission Engine Integration**
   - Permission Engine is available but not yet integrated with all sensitive actions
   - Currently implemented: Core permission checking, decorators
   - In progress: Full integration with all agents
   - Workaround: All actions currently require explicit approval

2. **MTBF Accuracy**
   - MTBF requires 24+ hours of operational data to be representative
   - Initial values may be 0 until system has runtime history
   - Monitor over time for accurate reliability metrics

3. **Logging Consistency**
   - Log files now centralized at `logs/agentjw.log`
   - Health check script updated to handle missing log files
   - Historical logs may exist in different locations

4. **Recovery Metrics**
   - MTTR tracking operational
   - Recovery simulation needs more test cases
   - Automatic recovery from all crash types not yet verified

## 🔜 Next Release (v0.9.0)

- Full Permission Engine integration
- Business OS features
- Enhanced recovery scenarios
- Complete logging consistency
- Multi-workspace support (preview)

---
**Last Updated**: July 17, 2026
**Status**: 🟢 Operational - Monitoring in Progress
