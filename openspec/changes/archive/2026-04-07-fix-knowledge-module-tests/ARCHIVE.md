# Change Archive: fix-knowledge-module-tests
**Archive Date**: 2026-04-07
**Schema**: spec-driven
**Status**: Completed ✅

## 变更概述
修复knowledge模块单元测试失败的核心问题：缺失`get_knowledge_base()`单例函数，导致Agent工具无法正确初始化知识库实例。

## 完成的任务
1. ✅ 在`nanobot/knowledge/__init__.py`中添加`get_knowledge_base()`单例函数实现
2. ✅ 同时添加`is_enabled()`函数检查知识库功能是否在配置中启用
3. ✅ 更新导出列表，暴露`get_knowledge_base`和`is_enabled`函数
4. ✅ 修复了Agent工具模块导入失败的问题

## 修复效果
- ✅ 解决了所有依赖知识库实例的工具测试失败问题
- ✅ 知识库工具现在可以正常被Agent调用
- ✅ 支持配置开关控制知识库功能启用状态

## 涉及文件修改
- `nanobot/knowledge/__init__.py`: 添加单例函数和导出