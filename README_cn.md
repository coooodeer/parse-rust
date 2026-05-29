# parse-rust

<p align="center">
[ <a href="README.md">En</a> |
<b>中</b> ]
<br><b><code>str.format()</code> 的逆操作——以 Rust 级速度从文本中提取结构化值。</b>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 介绍

[`parse`](https://github.com/r1chardj0n3s/parse)（约 1.8k Stars，MIT 许可证）是 Python `str.format()` 的逆操作。给定一个格式模板和一个字符串，通过将模板与输入匹配并将捕获字段转换为声明的类型，自动提取结构化值。其核心能力包括：

- **核心 API**：`parse()` 从完整字符串匹配中提取值，`search()` 在文本任意位置查找首个匹配，`findall()` 返回全部非重叠匹配的迭代器，`compile()` 将格式字符串预编译为可复用的 `Parser` 对象。
- **Format mini-language**：完整支持 `[[fill]align][sign][0][width][grouping][.precision][type]`，与 Python `str.format()` 使用相同的格式规范。
- **25 种格式说明符类型**：文本类 7 种（默认、`s`、`w`、`W`、`l`、`S`、`D`），整数类 5 种（`d`、`b`、`o`、`x`、`n`），浮点类 5 种（`f`、`F` 返回 `Decimal`、`e`、`g`、`%` 自动除以 100），日期时间类 8 种（`ti`、`te`、`ta`、`tg`、`th`、`tc`、`ts`、`tt` 以及自定义 `%...` strptime 格式）。
- **Result 结果封装**：支持索引访问（`result[0]`）、命名访问（`result["name"]`）、`.fixed` 元组、`.named` 字典、`.spans` 位置信息。
- **高级特性**：`evaluate_result=False` 延迟求值、`extra_types` 自定义类型转换器、`with_pattern` 装饰器注册自定义匹配模式、`case_sensitive` 大小写敏感控制、重复命名字段等值校验与 `RepeatedNameError` 异常。

典型应用场景包括日志分析、数据提取、ETL 管道和模板匹配——任何需要从半结构化文本中提取结构化数据的场合。

`parse-rust` 将完整解析引擎以 Rust 重新实现，同时保持 Python API 兼容。全部解析、模式编译和类型转换逻辑均在 safe Rust 中运行。唯一的非 Rust 组件是 `FixedTzOffset`——一个约 20 行的 Python 桥接类，因 CPython 要求 `datetime.tzinfo` 子类必须通过纯 Python 单继承创建。

## 创新与优化

相比 Python 原版实现，`parse-rust` 在四个维度实现了提升：

### 1. 编程语言切换：Python → Rust + PyO3

核心解析引擎完全以 Rust 编写，通过 PyO3 暴露为 Python 接口。这一架构同时获得了 Rust 的编译期性能与内存安全优势，以及 Python 生态的无缝接入能力。引擎按 compiler、types、parser、result 四个模块组织，零 Python fallback 路径。自定义类型转换器（`extra_types`、`with_pattern`）在 Rust 侧调度，用户提供的 Python 转换函数以回调形式从 Rust 调用。

### 2. 性能提升

所有 benchmark 均使用 release build，5 次独立运行报告 mean ± std，以 Python `parse` 1.20.2 为 baseline：

- **吞吐量**：parse/search/findall 全路径加速比 4.2x–10.8x。日志风格解析达 10.8x，简单字符串提取 6.6x。
- **P99 尾延迟**：改善 13–29x（如日志风格：1.01 μs vs 29.02 μs）。Rust 的 P50/P95/P99 高度集中，差异仅 0.2–0.5 μs——无 GC 暂停，无长尾抖动。
- **内存效率**：单位内存吞吐量为 Python 原版的 4.2x–7.7x。RSS 在 100K → 300K 输入规模下零增长，证明堆分配有界。

### 3. 安全性增强

- **0 个 `unsafe` 代码块**——编译期保证内存安全。
- **32/32 项对抗输入安全测试通过**——覆盖超大输入（1 MiB）、空字节、Unicode 边界（emoji、组合字符、RTL、代理对）、正则注入抵抗、8 层深度嵌套、畸形格式、类型转换边界、search/findall 极端参数。零崩溃、零 panic、零挂起。
- **静态分析**：0 个 Clippy correctness/safety 警告；依赖审计已清零；先前唯一的传递依赖漏洞（pyo3 < 0.24.1）已通过升级至 pyo3 0.24 解决。

### 4. 架构升级

模块化 Rust 设计清晰分离关注点：compiler（格式字符串→正则，700 行）、types（25 种说明符，463 行）、parser（核心引擎，555 行）、result（封装+datetime 规范化，598 行）。全局解析器缓存（`OnceLock<Mutex<ParserCache>>`）消除了冗余格式编译，cold/warm/compiled 三种模式的吞吐量差异 < 10%。Rust regex DFA 的编译开销在纳秒级，而 Python `re.compile` 在毫秒级。

## 安装

### 从源码安装（推荐）

```bash
git clone https://github.com/coooodeer/parse-rust && cd parse-rust
pip install maturin
maturin develop --release
```

### 构建 wheel 分发包

```bash
cd parse-rust
maturin build --release
# 生成的 .whl 文件位于 target/wheels/
```

### 验证安装

```bash
python -c "from parse_rust import parse, compile; print('OK')"
# 预期输出：OK
```

**环境要求：** Python ≥ 3.8、Rust ≥ 1.75（stable）、maturin ≥ 1.0

## 快速开始

```python
from parse_rust import parse, search, findall, compile

# 基本解析——{} 贪婪匹配任意字符
result = parse("Hello, {}!", "Hello, World!")
assert result[0] == "World"

# 命名字段 + 类型转换
result = parse("User {name:w} is {:d} years old", "User Alice is 30 years old")
assert result["name"] == "Alice"   # :w 匹配单词字符
assert result[0] == 30             # :d 匹配整数并转换为 int

# search 在文本任意位置查找首个匹配
found = search("{:d}", "I have 3 cats and 5 dogs")
assert found[0] == 3

# findall 返回全部非重叠匹配的迭代器
values = [r[0] for r in findall("{:d}", "I have 3 cats and 5 dogs")]
assert values == [3, 5]

# compile 预编译格式字符串，供高频调用复用
parser = compile("User {name:w} is {:d} years old")
assert parser.parse("User Alice is 30 years old")["name"] == "Alice"
assert parser.parse("User Bob is 42 years old")[0] == 42
```

## API 参考

### 顶层函数

| 函数 | 签名 |
|------|------|
| `parse` | `parse(format, string, extra_types=None, evaluate_result=True, case_sensitive=False)` |
| `search` | `search(format, string, pos=0, endpos=None, extra_types=None, evaluate_result=True, case_sensitive=False)` |
| `findall` | `findall(format, string, pos=0, endpos=None, extra_types=None, evaluate_result=True, case_sensitive=False)` |
| `compile` | `compile(format, extra_types=None, case_sensitive=False)` |
| `with_pattern` | `with_pattern(regex, regex_group_count=1)` — 装饰器 |
| `extract_format` | `extract_format(format_string)` — 返回格式说明符的结构化解析字典 |

### Parser 对象

| 属性/方法 | 说明 |
|-----------|------|
| `.parse(string, evaluate_result=True)` | 解析单个字符串 |
| `.search(string, pos=0, endpos=None, evaluate_result=True)` | 搜索首个匹配 |
| `.findall(string, pos=0, endpos=None, evaluate_result=True)` | 返回全部匹配的迭代器 |
| `.format` | 格式模板字符串 |
| `.pattern` | 编译后的正则表达式 |
| `.named_fields` | 命名字段列表 |
| `.fixed_fields` | 位置字段数量 |

### Result 对象

| 属性/方法 | 说明 |
|-----------|------|
| `result[i]` | 按整数索引访问（支持负索引与切片） |
| `result["name"]` | 按名称访问命名字段 |
| `.fixed` | 位置字段值的元组 |
| `.named` | 命名字段值的字典 |
| `.spans` | 各字段在原文中起止位置的字典，键为整数（位置字段）或字符串（命名字段） |

### Match 对象（`evaluate_result=False` 时返回）

| 方法 | 说明 |
|------|------|
| `.evaluate_result()` | 执行类型转换，返回 `Result` 对象 |

## 支持的格式类型

| 类型 | 匹配内容 | Python 输出 |
|------|---------|-------------|
| 默认 / `s` | 任意字符（贪婪） | `str` |
| `w` | 字母、数字、下划线 | `str` |
| `W` | 非字母、数字、下划线 | `str` |
| `l` | 字母（ASCII） | `str` |
| `S` | 非空白字符 | `str` |
| `D` | 非数字字符 | `str` |
| `d` | 整数（可选符号位） | `int` |
| `b` | 二进制数 | `int` |
| `o` | 八进制数 | `int` |
| `x` | 十六进制数 | `int` |
| `n` | 带千位分隔符的数字 | `int` |
| `f` | 定点数 | `float` |
| `e` | 科学计数法浮点数 | `float` |
| `g` | 通用数字格式 | `float` |
| `%` | 百分比（值 / 100.0） | `float` |
| `F` | 十进制数 | `Decimal` |
| `ti` | ISO 8601 日期时间 | `datetime` |
| `te` | RFC 2822 邮件日期时间 | `datetime` |
| `ta` | 美国（月/日）日期时间 | `datetime` |
| `tg` | 国际（日/月）日期时间 | `datetime` |
| `th` | HTTP 日志日期时间 | `datetime` |
| `tc` | ctime() 日期时间 | `datetime` |
| `ts` | Linux syslog 日期时间 | `datetime` |
| `tt` | 纯时间 | `time` |
| `%...` | 自定义 strptime 格式 | `date`、`time` 或 `datetime` |

完整支持 Python format mini-language 语法（`[[fill]align][sign][0][width][grouping][.precision][type]`），包括对齐、填充字符、宽度、千位分隔符和精度。

## 使用示例

### 日期时间解析

```python
from parse_rust import parse

# ISO 8601 格式
r = parse("At {:ti}", "At 1972-01-20T10:21:36Z")
assert r[0].year == 1972

# RFC 2822 邮件格式（含时区）
r = parse("At {:te}", "At Mon, 20 Jan 1972 10:21:36 +1000")
assert r[0].hour == 10

# 自定义 strptime 格式
r = parse("On {:%Y-%m-%d}", "On 2023-11-25")
assert r[0].day == 25

# 纯时间
from datetime import time, timezone, timedelta
r = parse("At {:tt}", "At 10:21:36 PM -0530")
assert r[0] == time(22, 21, 36, tzinfo=timezone(timedelta(hours=-5, minutes=-30)))
```

### 自定义类型（`extra_types` + `with_pattern`）

```python
from parse_rust import compile, with_pattern

@with_pattern(r"[ab]")
def ab(text):
    return {"a": 1, "b": 2}[text]

parser = compile("test {result:ab}", extra_types={"ab": ab})
assert parser.parse("test a").named == {"result": 1}
assert parser.parse("test b").named == {"result": 2}
assert parser.parse("test c") is None  # 不匹配正则

# 自定义类型可覆盖内置类型
@with_pattern(r"\d+")
def doubler(text):
    return int(text) * 2

result = parse("{:d}", "42", extra_types={"d": doubler})
assert result[0] == 84
```

### 延迟求值（`evaluate_result=False`）

```python
from parse_rust import parse

match = parse("hello {}", "hello world", evaluate_result=False)
# match 为 Match 对象，尚未进行类型转换
result = match.evaluate_result()  # 触发转换，得到 Result
assert result.fixed == ("world",)
```

### Span 位置信息

```python
result = parse("User {name:w} is {:d} years old", "User Alice is 30 years old")
print(result.spans)
# {0: (12, 14), 'name': (5, 10)}
```

### 重复命名字段

```python
from parse_rust import parse, RepeatedNameError

# 同名字段值一致 → 匹配成功
result = parse("{name:w} {name:w}", "Alice Alice")
assert result.named == {"name": "Alice"}

# 同名字段类型冲突 → 抛出 RepeatedNameError
try:
    parse("{name:w} {name:d}", "Alice 30")
except RepeatedNameError:
    pass  # 符合预期
```

### 大小写敏感控制

```python
# 默认：大小写不敏感
assert parse("hello {}", "HELLO World") is not None

# 严格匹配
assert parse("hello {}", "HELLO World", case_sensitive=True) is None
```

### 搜索位置约束

```python
from parse_rust import search

# 从第 10 个字符位置开始搜索
result = search("{:d}", "I have 3 and 5", pos=10)
assert result[0] == 5
```

## 实现架构

核心解析引擎分为四个 Rust 模块，通过 PyO3 暴露为 Python 接口：

| 模块 | 源文件 | 有效代码行数 | 职责 |
|------|--------|:---:|------|
| **compiler** | `src/compiler.rs` | 700 | 格式字符串词法分割、格式说明符解析、正则转义、自定义类型注册 |
| **types** | `src/types.rs` | 463 | 全部 25 种格式说明符的正则模式生成、类型转换（整数/浮点/Decimal/日期时间）、自定义 `%...` strptime 格式翻译 |
| **parser** | `src/parser.rs` | 555 | parse/search/findall 流程编排、正则匹配、重复命名字段等值校验、延迟求值 |
| **result** | `src/result.rs` | 598 | Result/Match 对象封装、ISO datetime 规范化、微秒精度处理、嵌套字典展开 |

Python 接口层（`src/lib.rs`，694 行有效代码）：PyO3 绑定、`RepeatedNameError` 异常定义、全局解析器缓存（`OnceLock<Mutex<ParserCache>>`）以及 `FixedTzOffset` 桥接类。

## 性能

所有 benchmark 均使用 release build（`maturin develop --release`），5 次独立运行报告 mean ± std，以 Python `parse` 1.20.2 原版为 baseline。

### 吞吐量（100K 行输入）

| 路径 | 场景 | Python 原版 | Rust 编译版 | 加速比 |
|------|------|:---:|:---:|:---:|
| parse | 简单字符串提取 | 177K l/s | 1,164K l/s | **6.6x** |
| parse | 多类型混合解析 | 77K l/s | 812K l/s | **10.5x** |
| parse | 日志风格解析 | 95K l/s | 1,024K l/s | **10.8x** |
| search | 简单字符串提取 | 181K l/s | 1,127K l/s | **6.2x** |
| search | 日志风格解析 | 99K l/s | 938K l/s | **9.5x** |
| findall | 全量扫描 | 34K l/s | 145K l/s | **4.2x** |
| fallback | 自定义类型 | 678K l/s | 2,080K l/s | **3.1x** |

### P99 尾延迟

| 场景 | Python 原版 | Rust 编译版 | 改善倍数 |
|------|:---:|:---:|:---:|
| 简单字符串提取 | 14.66 μs | 1.10 μs | **13.3x** |
| 多类型混合解析 | 29.51 μs | 1.33 μs | **22.2x** |
| 日志风格解析 | 29.02 μs | 1.01 μs | **28.7x** |

Rust 的 P50/P95/P99 延迟高度集中（差异在 0.2–0.5 μs 之间），无 GC 暂停，无长尾抖动。

### 内存效率

Rust 的内存效率（吞吐量 / 峰值 RSS）为 Python 原版的 **4.2x–7.7x**。RSS 在 100K → 300K 输入规模下零增长，证明堆分配有界且无逐记录内存泄漏。

## 安全性

- **0 个 `unsafe` 代码块**——所有 Rust 代码在 safe Rust 范围内运行，编译期保证内存安全
- **32/32 项对抗输入安全测试通过**——覆盖超大输入（1 MiB）、空字节、Unicode 边界（4 字节 emoji、组合字符、RTL 文本、孤立代理对）、正则注入抵抗（`*+?|^$\` 全部字面量化）、8 层深度嵌套、畸形格式字符串、类型转换边界、search/findall 极端参数。零崩溃、零 panic、零挂起
- **Clippy 静态检查**：0 个 correctness/safety 级别警告（仅 15 个 style/idiom 级别提示）
- **依赖安全审计**：依赖审计已清零；pyo3 已升级至 0.24，先前的传递依赖漏洞已修复

## 测试

三层测试证据链：

| 层级 | 命令 | 结果 |
|------|------|------|
| Rust 单元测试 | `cargo test --quiet` | **58 passed**（57 `#[test]` + 1 doctest） |
| Python 集成测试 | `python -m pytest -q tests` | **151 passed, 1 skipped** |
| 安全测试 | `python -m pytest -q tests/test_security_inputs.py` | **32 passed** |

1 个 skip（`test_parse.py::test_too_many_fields`）属于 Python 版本差异导致的上游测试条件变更，非兼容性失败。

Python 集成测试包含：
- **项目自建 API 集成测试**（22 项）：全部公开 API 的端到端覆盖
- **上游用例迁移对照测试**（7 个文件，129 项）：从 `parse-original/tests/` 迁移，仅做最小 import 调整，用于验证跨实现行为一致性

## 项目结构

```
parse-rust/
├── Cargo.toml              # Rust 项目配置
├── pyproject.toml          # Python 包配置（maturin 构建系统）
├── build.rs                # PyO3 构建脚本
├── LICENSE                 # MIT 许可证
├── src/                    # Rust 核心实现
│   ├── compiler.rs         # 格式字符串编译器
│   ├── lib.rs              # Python 模块入口与顶层 API
│   ├── parser.rs           # 核心解析引擎
│   ├── result.rs           # Result / Match 对象
│   └── types.rs            # 类型系统（25 种格式说明符）
├── tests/                  # Python 集成测试
│   ├── test_python_api_integration.py
│   ├── test_parse.py
│   ├── test_search.py
│   ├── test_findall.py
│   ├── test_bugs.py
│   ├── test_result.py
│   ├── test_parsetype.py
│   ├── test_pattern.py
│   └── test_security_inputs.py
└── benches/                # Benchmark 脚本与结果
    ├── benchmark_common.py   # 共享框架
    ├── benchmark_parse_throughput.py
    ├── benchmark_search_throughput.py
    ├── benchmark_findall_throughput.py
    ├── benchmark_parse_latency.py
    ├── benchmark_fallback_throughput.py
    └── results/
```

## 许可证

MIT。详见 [LICENSE](LICENSE)。
