# Git 提交规范

本文档定义了项目的 Git 提交规范，包括分支管理、提交信息格式、代码审查流程等，以确保团队协作的一致性和代码质量。

## 目录

- [分支管理策略](#分支管理策略)
- [分支命名规范](#分支命名规范)
- [提交信息规范](#提交信息规范)
- [合并到主分支流程](#合并到主分支流程)
- [代码审查流程](#代码审查流程)
- [发布流程](#发布流程)
- [Git 最佳实践](#git-最佳实践)
- [常见问题](#常见问题)

---

## 分支管理策略

本项目采用 **Git Flow** 工作流，主要包含以下分支类型：

### 主分支

| 分支名称 | 用途 | 保护规则 |
|---------|------|---------|
| `main` | 主分支，始终保持稳定可发布状态 | 禁止直接推送，必须通过 Pull Request 合并 |
| `develop` | 开发分支，集成最新的开发功能 | 禁止直接推送，必须通过 Pull Request 合并 |

### 辅助分支

| 分支类型 | 命名前缀 | 生命周期 | 合并目标 |
|---------|---------|---------|---------|
| 功能分支 | `feature/` | 短期 | `develop` |
| 修复分支 | `bugfix/` | 短期 | `develop` 或 `main`（紧急修复） |
| 热修复分支 | `hotfix/` | 短期 | `main` 和 `develop` |
| 发布分支 | `release/` | 中期 | `main` 和 `develop` |
| 实验分支 | `experiment/` | 短期 | 可能被废弃 |

---

## 分支命名规范

### 功能分支

用于开发新功能，从 `develop` 分支创建。

**格式：** `feature/<功能描述>`

**示例：**
```
feature/add-log-viewer
feature/implement-data-replay
feature/custom-widgets-dashboard
```

### 修复分支

用于修复非紧急的 Bug，从 `develop` 分支创建。

**格式：** `bugfix/<问题描述>`

**示例：**
```
bugfix/fix-memory-leak
bugfix/resolve-ui-freeze
bugfix/correct-csv-parsing
```

### 热修复分支

用于紧急修复生产环境的严重 Bug，从 `main` 分支创建。

**格式：** `hotfix/<问题描述>`

**示例：**
```
hotfix/critical-security-fix
hotfix/emergency-data-loss-fix
```

### 发布分支

用于准备发布新版本，从 `develop` 分支创建。

**格式：** `release/<版本号>`

**示例：**
```
release/v1.0.0
release/v2.1.3
```

### 实验分支

用于实验性功能或技术验证，从 `develop` 分支创建。

**格式：** `experiment/<实验描述>`

**示例：**
```
experiment/try-new-plotting-library
experiment/performance-optimization-test
```

---

## 提交信息规范

### 提交信息格式

采用 **Conventional Commits** 规范：

```
<类型>(<范围>): <简短描述>

<详细描述>

<页脚>
```

### 提交类型

| 类型 | 说明 | 示例 |
|-----|------|------|
| `feat` | 新功能 | `feat(log-viewer): add date filtering` |
| `fix` | 修复 Bug | `fix(data-replay): resolve CSV parsing error` |
| `docs` | 文档更新 | `docs(readme): update installation guide` |
| `style` | 代码格式调整（不影响功能） | `style(components): format code with black` |
| `refactor` | 重构（既不是新功能也不是修复） | `refactor(utils): simplify logger initialization` |
| `perf` | 性能优化 | `perf(plotting): optimize data rendering` |
| `test` | 测试相关 | `test(calib-tool): add unit tests for calibration` |
| `chore` | 构建/工具链相关 | `chore(deps): update PyQt5 to version 5.15.0` |
| `revert` | 回滚之前的提交 | `revert: feat(add-feature)` |

### 提交范围

范围用于说明提交影响的模块或组件：

- `log-viewer` - 日志查看器
- `data-replay` - 数据回放工具
- `rt-data-plot` - 实时数据绘图
- `calib-tool` - 校准工具
- `bus-data-monitor` - 总线数据监控
- `custom-widgets` - 自定义控件
- `net-manager` - 网络管理
- `resource-query` - 资源查询
- `xml-editor` - XML 编辑器
- `bulb-monitor` - 灯泡状态监控
- `utils` - 工具类
- `docs` - 文档
- `build` - 构建配置

### 提交示例

#### 简单提交

```
feat(log-viewer): add log filtering by level

Users can now filter logs by INFO, WARNING, ERROR levels
```

#### 完整提交

```
feat(data-replay): implement CSV data export

Add functionality to export replayed data to CSV format:
- Support exporting current view data
- Include timestamp and value columns
- Add export button to toolbar

Closes #123
```

#### 修复提交

```
fix(rt-data-plot): resolve memory leak in real-time plotting

The issue was caused by not properly clearing plot data
when switching between datasets. Now data is cleared before
loading new data.

Fixes #456
```

#### 破坏性变更

```
feat(calib-tool): update calibration data format

BREAKING CHANGE: Calibration configuration file format has changed.
Old configuration files need to be migrated to the new format.
A migration script has been provided in scripts/migrate_calib.py
```

---

## 合并到主分支流程

### 功能分支合并到 develop

1. **创建功能分支**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **开发和提交**
   ```bash
   git add .
   git commit -m "feat(module): your commit message"
   ```

3. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **创建 Pull Request**
   - 在 GitHub/GitLab 上创建 PR
   - 标题格式：`feat(module): your feature description`
   - 填写 PR 模板
   - 关联相关 Issue

5. **代码审查**
   - 至少需要 1 位审查者批准
   - 通过所有 CI 检查
   - 解决审查意见

6. **合并 PR**
   - 使用 **Squash and merge** 方式合并
   - 保持提交历史清晰

7. **删除分支**
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

### 发布分支合并流程

1. **创建发布分支**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/v1.0.0
   ```

2. **发布准备**
   - 更新版本号
   - 更新 CHANGELOG.md
   - 修复发现的 Bug
   - 更新文档

3. **合并到 main**
   ```bash
   git checkout main
   git merge release/v1.0.0
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin main --tags
   ```

4. **合并回 develop**
   ```bash
   git checkout develop
   git merge release/v1.0.0
   git push origin develop
   ```

5. **删除发布分支**
   ```bash
   git branch -d release/v1.0.0
   git push origin --delete release/v1.0.0
   ```

### 热修复分支合并流程

1. **创建热修复分支**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-fix
   ```

2. **修复和测试**

3. **合并到 main**
   ```bash
   git checkout main
   git merge hotfix/critical-fix
   git tag -a v1.0.1 -m "Hotfix version 1.0.1"
   git push origin main --tags
   ```

4. **合并回 develop**
   ```bash
   git checkout develop
   git merge hotfix/critical-fix
   git push origin develop
   ```

5. **删除热修复分支**
   ```bash
   git branch -d hotfix/critical-fix
   git push origin --delete hotfix/critical-fix
   ```

---

## 代码审查流程

### Pull Request 模板

创建 PR 时应填写以下信息：

```markdown
## 变更类型
- [ ] 新功能
- [ ] Bug 修复
- [ ] 重构
- [ ] 文档更新
- [ ] 性能优化
- [ ] 其他

## 变更描述
简要描述本次变更的内容和目的

## 测试情况
- [ ] 已添加单元测试
- [ ] 已通过现有测试
- [ ] 已进行手动测试
- [ ] 测试覆盖率未降低

## 关联 Issue
Closes #123

## 检查清单
- [ ] 代码符合项目风格规范
- [ ] 已更新相关文档
- [ ] 没有引入新的警告
- [ ] 已通过 CI 检查
- [ ] 已进行代码自审
```

### 审查要点

审查者应关注以下方面：

1. **功能正确性**
   - 代码是否实现了预期功能
   - 边界情况是否处理
   - 错误处理是否完善

2. **代码质量**
   - 代码结构是否清晰
   - 是否遵循项目规范
   - 是否有重复代码
   - 命名是否合理

3. **性能影响**
   - 是否引入性能问题
   - 内存使用是否合理

4. **测试覆盖**
   - 是否有足够的测试
   - 测试用例是否全面

5. **文档完整性**
   - 是否更新了相关文档
   - 代码注释是否充分

### 审查反馈

- 提供建设性的反馈意见
- 指出问题的同时给出改进建议
- 使用代码评论功能进行具体说明
- 必要时请求变更后再审查

---

## 发布流程

### 版本号规范

遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)：

```
主版本号.次版本号.修订号
```

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 发布检查清单

在发布新版本前，确保：

- [ ] 所有测试通过
- [ ] CHANGELOG.md 已更新
- [ ] 版本号已更新
- [ ] 文档已同步更新
- [ ] 无未解决的严重 Bug
- [ ] 性能指标符合预期
- [ ] 已进行回归测试

### 发布步骤

1. **更新版本号**
   ```bash
   # 更新 pyproject.toml 中的版本号
   ```

2. **更新 CHANGELOG**
   ```markdown
   ## [1.0.0] - 2025-02-25

   ### Added
   - Log viewer with date filtering
   - Data replay functionality
   - Real-time data plotting

   ### Fixed
   - CSV parsing error handling
   - Memory leak in plotting

   ### Changed
   - Improved UI responsiveness
   ```
   
3. **创建 Git 标签**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

4. **构建发布包**
   ```bash
   python -m build
   ```

5. **发布到 PyPI（可选）**
   ```bash
   twine upload dist/*
   ```

6. **创建 GitHub Release**
   - 上传构建产物
   - 附带发布说明
   - 关联相关 Issue

---

## Git 最佳实践

### 提交频率

- **小而频繁**：每个提交应该是一个完整的逻辑单元
- **原子性**：一个提交只做一件事
- **可测试**：每个提交都应该能独立测试

### 提交历史

- **保持清晰**：使用有意义的提交信息
- **避免合并提交**：在功能分支上使用 rebase 保持历史线性
- **清理历史**：合并前使用 `git rebase -i` 整理提交

### 分支管理

- **及时同步**：定期从上游分支拉取最新代码
- **保持分支简短**：功能分支生命周期不宜过长
- **及时删除**：合并后及时删除已完成的分支

### 冲突解决

1. **拉取最新代码**
   ```bash
   git fetch origin
   git rebase origin/develop
   ```

2. **解决冲突**
   - 手动编辑冲突文件
   - 标记冲突已解决
   ```bash
   git add <resolved-file>
   git rebase --continue
   ```

3. **测试验证**
   - 确保功能正常
   - 运行测试套件

### 常用 Git 命令

```bash
# 查看状态
git status

# 查看历史
git log --oneline --graph --all

# 暂存更改
git stash
git stash pop

# 撤销提交
git reset --soft HEAD~1  # 保留更改
git reset --hard HEAD~1  # 丢弃更改

# 修改最后一次提交
git commit --amend

# 查看差异
git diff
git diff --staged

# 查看远程
git remote -v

# 清理
git clean -fd
```

---

## 常见问题

### Q: 如何修改已经推送的提交信息？

**A:**
```bash
git commit --amend
git push origin <branch-name> --force
```

**注意**：避免修改已共享的提交历史，仅在个人分支上使用。

### Q: 如何合并多个提交？

**A:**
```bash
git rebase -i HEAD~n  # n 为要合并的提交数
```

在编辑器中将 `pick` 改为 `squash` 或 `s`，保存后编辑合并后的提交信息。

### Q: 如何恢复误删的分支？

**A:**
```bash
git reflog  # 查找分支的最后一次提交
git checkout -b <branch-name> <commit-hash>
```

### Q: 如何撤销已合并的 PR？

**A:**
```bash
# 创建回滚提交
git revert -m 1 <merge-commit-hash>
git push origin <branch-name>
```

### Q: 如何处理大文件？

**A:**
```bash
# 使用 Git LFS
git lfs track "*.h5"
git add .gitattributes
git add <large-file>
git commit -m "Add large file with LFS"
```

### Q: 如何查看某个文件的修改历史？

**A:**
```bash
git log --follow -- <file-path>
git show <commit-hash>:<file-path>
```

---

## 工具推荐

### 提交信息工具

- **Commitizen**：交互式提交信息生成
- **Conventional Changelog**：自动生成 CHANGELOG
- **Husky**：Git hooks 管理

### 代码质量工具

- **Black**：Python 代码格式化
- **Flake8**：Python 代码检查
- **Pylint**：Python 代码质量分析
- **MyPy**：Python 类型检查

### Git GUI 工具

- **GitKraken**：跨平台 Git 客户端
- **SourceTree**：免费 Git GUI
- **GitHub Desktop**：GitHub 官方客户端

---

## 附录

### 提交信息速查表

```
feat: 新功能
fix: 修复 Bug
docs: 文档
style: 格式
refactor: 重构
perf: 性能
test: 测试
chore: 构建/工具
revert: 回滚
```

### 分支操作速查表

```bash
# 创建分支
git checkout -b feature/new-feature

# 切换分支
git checkout develop

# 删除本地分支
git branch -d feature/old-feature

# 删除远程分支
git push origin --delete feature/old-feature

# 查看所有分支
git branch -a

# 同步远程分支
git fetch --all
git prune
```

---

**最后更新：** 2025-02-25

**维护者：** SanXiaoXing
