# Writing Good Tests（好测试的可证伪性纪律）

> 2026-09-20 引入，源自 superpowers v6.2.0（原 testing-anti-patterns.md 重写为正面目录）。
> 三条硬规则让测试**真的在测东西**——能被弄红的好测试才有价值。

## 三条硬规则

### 1. 说出哪个生产变更会让这个测试失败

写每个测试前（或评审时）回答：**"我要改掉生产代码里的什么，这个测试才会红？"**

- 答不出来 = 测试没有绑定任何行为 = 删掉或重写。
- **string-presence trap（字符串在场陷阱）**：测试只断言输出里"包含某段文字"，实现换成 `print("成功")` 也能过——它测的是字符串在场，不是行为。修法：断言行为结果（状态变化、返回值、副作用），不断言文案。

```python
# ❌ string-presence trap：改掉任何真实逻辑它照样绿
def test_login_success():
    result = login("u", "p")
    assert "success" in result.message   # 文案在场 ≠ 行为正确

# ✅ 说出会弄红它的变更："改掉 token 签发逻辑它会红"
def test_login_success():
    result = login("u", "p")
    assert result.token is not None
    assert verify_token(result.token).user_id == "u"
```

### 2. 期望值独立于被测代码推导

期望值来自**需求/规格**，不是把实现的输出抄进测试。

- **copy-the-implementation trap（照抄实现陷阱）**：跑一遍实现、把输出粘进 `assert`——测试永远绿，因为它就是实现的镜子。实现错了，测试陪绑。
- 修法：期望值手算/从规格推导；复杂期望用独立算法或已知常量交叉验证。

```python
# ❌ 镜子测试：期望来自实现输出，实现错了它也对
def test_discount():
    assert calculate_discount(100, "vip") == calculate_discount(100, "vip")

# ✅ 期望独立推导：规格说 VIP 8 折
def test_discount():
    assert calculate_discount(100, "vip") == 80   # 来自规格，不来自实现
```

### 3. Mutation check（变异检查）：改坏生产代码，确认测试真的红

对关键测试抽样做一次：**故意改坏一行生产代码（off-by-one、条件取反、返回值 +1），跑测试——它必须红。**

- 测试不红 = 它没覆盖这行/这个行为 = 假覆盖。
- 全绿后随手恢复代码。CI 里可用 mutmut（Python）、Stryker（JS/TS）系统化做。
- 本仓库教训印证（pytest 污染事故）：单跑过、全量挂——先确认测试自身可证伪，再查污染。

## 应用清单

写完 / 评审一个测试时过一遍：

- [ ] 我能说出"改掉哪行生产代码它变红"吗？
- [ ] 期望值是从规格推导的，不是从实现抄的？
- [ ] 关键路径测试做过一次 mutation check？
- [ ] 断言的是行为（状态/返回/副作用），不是文案在场？

## 与既有纪律的关系

- 与 tdd-full.md 互补：TDD 管**顺序**（先红后绿），本文管**红得真不真**（失败是否绑定行为）。
- 与红线 R3.1（根因分析）同源思想：测试也要经得起"这个失败说明了什么"的追问。
- flaky 测试排查见 systematic-debugging/condition-based-waiting.md；本文件不处理时序问题。
