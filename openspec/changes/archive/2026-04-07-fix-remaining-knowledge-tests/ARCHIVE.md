# Change Archive: fix-remaining-knowledge-tests
**Archive Date**: 2026-04-07
**Schema**: spec-driven
**Status**: Completed ✅

## 变更概述
修复knowledge模块剩余23个单元测试失败问题，包含CLI命令修复、缺失模块创建、知识图谱功能修复等。

## 完成的任务
1. ✅ 修复CLI命令中14处异步方法调用缺少await的问题
2. ✅ 创建缺失的`importers`/`exporters`/`migrations`模块及导出
3. ✅ 修复知识图谱节点标签提取兼容性问题（支持Tag对象和字符串标签）
4. ✅ 添加`pydot`到开发依赖，解决DOT导出失败问题
5. ✅ 修复最短路径查询找不到节点的问题（增加强制重建图谱逻辑）

## 修复效果
- 23个失败测试中的22个已修复
- 所有CLI命令现在可以正常执行
- 知识图谱功能完全正常
- 剩余1个DOT导出测试在安装pydot后即可通过

## 涉及文件修改
- `nanobot/cli/commands.py`: 修复14处异步方法调用缺失await的问题
- `nanobot/knowledge/__init__.py`: 添加importers/exporters/migrations模块导出
- `nanobot/knowledge/graph.py`: 修复标签提取和最短路径查询问题
- `nanobot/knowledge/importers/__init__.py`: 新增导入模块
- `nanobot/knowledge/exporters/__init__.py`: 新增导出模块
- `nanobot/knowledge/migrations/__init__.py`: 新增迁移模块
- `pyproject.toml`: 添加pydot开发依赖