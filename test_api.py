"""
智能食谱 API 完整测试脚本 v2.0

覆盖全部 6 大模块 49 个核心接口：
  User(11) | Ingredient(7) | Recipe(12) | Shopping(7) | Community(7) | Nutrition(5)

用法：
  uv run python test_api.py
"""
import sys
import time
import json
import requests
from datetime import date

# ── Windows UTF-8 输出 ──────────────────────────────────────
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "http://127.0.0.1:8000"

# ── 全局共享状态 ────────────────────────────────────────────
state = {
    "access_token": None,
    "refresh_token": None,
    "headers": {},
    "user_id": None,
    "second_user_id": None,
    "recipe_id": None,
    "ingredient_id": None,
    "shopping_item_id": None,
    "share_token": None,
    "post_id": None,
    "comment_id": None,
    "diary_id": None,
}

# ── 结果统计 ────────────────────────────────────────────────
results = {"pass": 0, "fail": 0, "skip": 0, "cases": []}
_start_time = time.time()


# ══════════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════════

def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def pp(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def run(case_id, name, fn):
    """执行一个测试用例并记录结果"""
    try:
        fn()
        results["pass"] += 1
        results["cases"].append({"id": case_id, "name": name, "status": "PASS"})
        print(f"  [PASS] {case_id} {name}")
    except AssertionError as e:
        results["fail"] += 1
        results["cases"].append({"id": case_id, "name": name, "status": "FAIL", "error": str(e)})
        print(f"  [FAIL] {case_id} {name}  ->  {e}")
    except Exception as e:
        results["fail"] += 1
        results["cases"].append({"id": case_id, "name": name, "status": "ERROR", "error": str(e)})
        print(f"  [ERROR] {case_id} {name}  ->  {e}")


def skip(case_id, name, reason=""):
    results["skip"] += 1
    results["cases"].append({"id": case_id, "name": name, "status": "SKIP", "reason": reason})
    print(f"  [SKIP] {case_id} {name}  ({reason})")


def assertOK(resp, msg=""):
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:200]} {msg}"
    data = resp.json()
    assert data.get("code") == 200, f"code={data.get('code')}, msg={data.get('message')} {msg}"
    return data


def get(url, **kwargs):
    return requests.get(f"{BASE_URL}{url}", headers=state["headers"], **kwargs)


def post(url, **kwargs):
    return requests.post(f"{BASE_URL}{url}", headers=state["headers"], **kwargs)


def patch(url, **kwargs):
    return requests.patch(f"{BASE_URL}{url}", headers=state["headers"], **kwargs)


def delete(url, **kwargs):
    return requests.delete(f"{BASE_URL}{url}", headers=state["headers"], **kwargs)


# ══════════════════════════════════════════════════════════════
# 模块 1：User（11 个）
# ══════════════════════════════════════════════════════════════

def test_module_user():
    sep("MODULE 1: USER  (11 cases)")

    ts = str(int(time.time()))[-6:]  # 时间戳后缀，避免用户名冲突

    def u01():
        r = requests.post(f"{BASE_URL}/api/user/register/", json={
            "username": f"tester_{ts}",
            "password": "Test@1234",
            "password_confirm": "Test@1234",
            "nickname": f"测试用户{ts}"
        })
        # 200 成功，或 400（用户已存在）都不算测试失败
        assert r.status_code in (200, 400), f"HTTP {r.status_code}"
        if r.status_code == 200:
            print(f"    -> 注册成功 username=tester_{ts}")
    run("U-01", "用户注册", u01)

    def u02():
        r = requests.post(f"{BASE_URL}/api/user/register/", json={
            "username": f"tester2_{ts}",
            "password": "Test@1234",
            "password_confirm": "Test@1234",
            "nickname": f"第二用户{ts}"
        })
        assert r.status_code in (200, 400), f"HTTP {r.status_code}"
    run("U-02", "注册第二用户（关注测试）", u02)

    def u03():
        r = requests.post(f"{BASE_URL}/api/user/login/", json={
            "username": f"tester_{ts}",
            "password": "Test@1234"
        })
        d = assertOK(r)
        state["access_token"] = d["data"]["access"]
        state["refresh_token"] = d["data"]["refresh"]
        state["headers"] = {"Authorization": f"Bearer {state['access_token']}"}
        uid = d["data"].get("profile", {}).get("id") or d["data"].get("user", {}).get("id")
        if uid:
            state["user_id"] = uid
        print(f"    -> Token 已获取, user_id={uid}")
    run("U-03", "密码登录并获取 Token", u03)

    def u04():
        r = requests.post(f"{BASE_URL}/api/user/token/refresh/", json={
            "refresh": state["refresh_token"]
        })
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:100]}"
        data = r.json()
        # simplejwt 可能直接返回 {"access": "..."} 或包装格式 {"code":200,"data":{"access":"..."}}
        new_token = (data.get("data") or {}).get("access") or data.get("access")
        assert new_token, f"未获取到新 access token: {data}"
        state["access_token"] = new_token
        state["headers"] = {"Authorization": f"Bearer {new_token}"}
        print(f"    -> Token 刷新成功")
    run("U-04", "Token 刷新", u04)

    def u05():
        r = get("/api/user/profile/")
        d = assertOK(r)
        uid = d["data"].get("user", {}).get("id") or d["data"].get("id")
        if uid:
            state["user_id"] = uid
        print(f"    -> nickname={d['data'].get('nickname')}, user_id={uid}")
    run("U-05", "获取用户档案", u05)

    def u06():
        r = patch("/api/user/profile/", json={"nickname": f"更新昵称{ts}"})
        assertOK(r)
        print(f"    -> 档案更新成功")
    run("U-06", "更新用户档案(PATCH)", u06)

    def u07():
        r = requests.post(f"{BASE_URL}/api/user/send-code/", json={"phone": "13800138000"})
        assert r.status_code == 200, f"HTTP {r.status_code}"
        d = r.json()
        code = d.get("data", {}).get("code")
        print(f"    -> 验证码已发送, code={code}")
    run("U-07", "发送短信验证码", u07)

    def u08():
        r = post("/api/user/health-profile/", json={
            "health_goal": "weight_loss",
            "daily_calories_target": 1800,
            "dietary_preference": ["low_fat"],
            "allergies": []
        })
        assertOK(r)
        print(f"    -> 健康档案已更新")
    run("U-08", "更新健康档案", u08)

    def u09():
        r = get("/api/user/health-profile/")
        d = assertOK(r)
        print(f"    -> health_goal={d['data'].get('health_goal')}")
    run("U-09", "获取健康档案", u09)

    def u10():
        # 查找第二个用户的 id
        r = requests.post(f"{BASE_URL}/api/user/login/", json={
            "username": f"tester2_{ts}",
            "password": "Test@1234"
        })
        if r.status_code != 200:
            raise AssertionError("第二用户登录失败，无法测试关注")
        second_data = r.json()
        # 获取第二用户的 user id
        r2 = requests.get(f"{BASE_URL}/api/user/profile/", headers={
            "Authorization": f"Bearer {second_data['data']['access']}"
        })
        if r2.status_code == 200:
            uid2 = r2.json()["data"].get("user", {}).get("id") or r2.json()["data"].get("id")
            state["second_user_id"] = uid2
        else:
            raise AssertionError("无法获取第二用户 id")
        r = post(f"/api/user/{uid2}/follow/")
        assertOK(r)
        print(f"    -> 已关注 user_id={uid2}")
    run("U-10", "关注用户", u10)

    def u11():
        r = get("/api/user/following/")
        d = assertOK(r)
        count = len(d["data"]) if isinstance(d["data"], list) else d["data"].get("count", 0)
        print(f"    -> 关注列表共 {count} 人")
    run("U-11", "获取我的关注列表", u11)


# ══════════════════════════════════════════════════════════════
# 模块 2：Ingredient（7 个）
# ══════════════════════════════════════════════════════════════

def test_module_ingredient():
    sep("MODULE 2: INGREDIENT  (7 cases)")

    def i01():
        r = get("/api/ingredient/")
        d = assertOK(r)
        count = d["data"].get("count", 0)
        print(f"    -> 食材总数={count}")
        if count > 0:
            first = d["data"]["results"][0]
            state["ingredient_id"] = first["id"]
            print(f"    -> 取 id={first['id']} name={first['name']} 用于后续测试")
    run("I-01", "食材列表", i01)

    def i02():
        if not state["ingredient_id"]:
            raise AssertionError("无食材数据，跳过详情测试")
        r = get(f"/api/ingredient/{state['ingredient_id']}/")
        d = assertOK(r)
        print(f"    -> name={d['data'].get('name')} category={d['data'].get('category')}")
    run("I-02", "食材详情", i02)

    def i03():
        r = get("/api/ingredient/search/", params={"q": "鸡"})
        d = assertOK(r)
        cnt = d["data"].get("count", len(d["data"].get("results", [])))
        print(f"    -> 搜索'鸡'结果数={cnt}")
    run("I-03", "食材搜索", i03)

    def i04():
        r = get("/api/ingredient/seasonal/")
        d = assertOK(r)
        cnt = len(d["data"]) if isinstance(d["data"], list) else d["data"].get("count", 0)
        print(f"    -> 应季食材数={cnt}")
    run("I-04", "应季食材", i04)

    def i05():
        if not state["ingredient_id"]:
            raise AssertionError("无食材数据")
        r = requests.post(f"{BASE_URL}/api/ingredient/nutrition-calculate/", json={
            "ingredient_id": state["ingredient_id"],
            "quantity_grams": 200
        })
        d = assertOK(r)
        print(f"    -> calories={d['data'].get('calories')}")
    run("I-05", "营养计算", i05)

    def i06():
        r = requests.post(f"{BASE_URL}/api/ingredient/recommend/", json={
            "ingredients": ["西红柿", "鸡蛋"]
        })
        d = assertOK(r)
        cnt = len(d["data"]) if isinstance(d["data"], list) else d["data"].get("count", 0)
        print(f"    -> 推荐食谱数={cnt}")
    run("I-06", "基于食材推荐食谱", i06)

    def i07():
        r = get("/api/ingredient/history/")
        d = assertOK(r)
        cnt = len(d["data"]) if isinstance(d["data"], list) else d["data"].get("count", 0)
        print(f"    -> 识别历史记录数={cnt}")
    run("I-07", "食材识别历史", i07)


# ══════════════════════════════════════════════════════════════
# 模块 3：Recipe（12 个）
# ══════════════════════════════════════════════════════════════

def test_module_recipe():
    sep("MODULE 3: RECIPE  (12 cases)")

    def r01():
        r = get("/api/recipe/")
        d = assertOK(r)
        print(f"    -> 食谱总数={d['data'].get('count', 0)}")
    run("R-01", "食谱列表", r01)

    def r02():
        r = post("/api/recipe/create/", json={
            "name": "自动测试食谱_西红柿炒蛋",
            "difficulty": "easy",
            "cooking_time": 15,
            "servings": 2,
            "category": "lunch",
            "cuisine_type": "chinese",
            "description": "测试用自动创建的食谱，简单美味的家常菜",
            "tags": ["快手", "家常", "简单"],
            "total_calories": 320,
            "is_published": True
        })
        d = assertOK(r)
        state["recipe_id"] = d["data"]["id"]
        print(f"    -> 创建成功 recipe_id={state['recipe_id']}")
    run("R-02", "创建食谱", r02)

    def r03():
        if not state["recipe_id"]:
            raise AssertionError("无食谱 id")
        r = get(f"/api/recipe/{state['recipe_id']}/")
        d = assertOK(r)
        print(f"    -> name={d['data'].get('name')} likes={d['data'].get('likes')}")
    run("R-03", "食谱详情", r03)

    def r04():
        if not state["recipe_id"]:
            raise AssertionError("无食谱 id")
        r = patch(f"/api/recipe/{state['recipe_id']}/update/", json={
            "description": "测试更新：简单美味的家常菜（已更新）"
        })
        assertOK(r)
        print(f"    -> 食谱更新成功")
    run("R-04", "更新食谱(PATCH)", r04)

    def r05():
        r = get("/api/recipe/search/", params={"q": "西红柿"})
        d = assertOK(r)
        cnt = d["data"].get("count", 0)
        print(f"    -> 搜索'西红柿'结果数={cnt}")
    run("R-05", "食谱搜索", r05)

    def r06():
        r = get("/api/recipe/hot/", params={"limit": 5})
        d = assertOK(r)
        cnt = len(d["data"]) if isinstance(d["data"], list) else d["data"].get("count", 0)
        print(f"    -> 热门食谱数={cnt}")
    run("R-06", "热门食谱", r06)

    def r07():
        r = get("/api/recipe/recommend/")
        d = assertOK(r)
        # data 可能是 list 或 dict（含 results）
        raw = d["data"]
        cnt = len(raw) if isinstance(raw, list) else raw.get("count", len(raw.get("results", [])))
        print(f"    -> 推荐食谱数={cnt}")
    run("R-07", "个性化推荐", r07)

    def r08():
        if not state["recipe_id"]:
            raise AssertionError("无食谱 id")
        r = post(f"/api/recipe/{state['recipe_id']}/like/")
        d = assertOK(r)
        print(f"    -> {d['message']}")
    run("R-08", "点赞食谱", r08)

    def r09():
        if not state["recipe_id"]:
            raise AssertionError("无食谱 id")
        r = post(f"/api/recipe/{state['recipe_id']}/favorite/")
        d = assertOK(r)
        print(f"    -> {d['message']}")
    run("R-09", "收藏食谱", r09)

    def r10():
        r = get("/api/recipe/favorites/")
        d = assertOK(r)
        cnt = d["data"].get("count", 0)
        print(f"    -> 收藏总数={cnt}")
    run("R-10", "收藏列表", r10)

    def r11():
        r = get("/api/recipe/my-recipes/")
        d = assertOK(r)
        cnt = d["data"].get("count", 0)
        print(f"    -> 我的食谱数={cnt}")
    run("R-11", "我的食谱", r11)

    def r12():
        r = get("/api/recipe/history/")
        d = assertOK(r)
        raw = d["data"]
        cnt = len(raw) if isinstance(raw, list) else raw.get("count", len(raw.get("results", [])))
        print(f"    -> 浏览历史数={cnt}")
    run("R-12", "浏览历史", r12)


# ══════════════════════════════════════════════════════════════
# 模块 4：Shopping（7 个）
# ══════════════════════════════════════════════════════════════

def test_module_shopping():
    sep("MODULE 4: SHOPPING LIST  (7 cases)")

    def s01():
        r = get("/api/shopping-list/")
        d = assertOK(r)
        cnt = len(d["data"]) if isinstance(d["data"], list) else d["data"].get("count", 0)
        print(f"    -> 购物清单条目数={cnt}")
    run("S-01", "获取购物清单", s01)

    def s02():
        if not state["ingredient_id"]:
            raise AssertionError("无食材 id，跳过")
        r = post("/api/shopping-list/", json={
            "ingredient_id": state["ingredient_id"],
            "quantity": "2",
            "unit": "个"
        })
        d = assertOK(r)
        state["shopping_item_id"] = d["data"]["id"]
        print(f"    -> 添加购物项 id={state['shopping_item_id']}")
    run("S-02", "添加购物项", s02)

    def s03():
        if not state["shopping_item_id"]:
            raise AssertionError("无购物项 id")
        r = patch(f"/api/shopping-list/{state['shopping_item_id']}/", json={
            "is_purchased": True
        })
        assertOK(r)
        print(f"    -> 已标记为已购买")
    run("S-03", "更新购物项（标记已购）", s03)

    def s04():
        if not state["recipe_id"]:
            raise AssertionError("无食谱 id")
        r = post("/api/shopping-list/generate/", json={
            "recipe_id": state["recipe_id"]
        })
        # 食谱无食材时返回 400（正常业务逻辑），200 或 400 均视为接口正常
        assert r.status_code in (200, 400), f"HTTP {r.status_code}"
        msg = r.json().get("message", "")
        print(f"    -> {r.status_code} {msg}")
    run("S-04", "从食谱生成购物清单", s04)

    def s05():
        r = post("/api/shopping-list/share/", json={
            "permission": "read",
            "days": 7
        })
        d = assertOK(r)
        state["share_token"] = d["data"].get("token")
        print(f"    -> 分享 token={state['share_token'][:20]}...")
    run("S-05", "创建分享链接", s05)

    def s06():
        if not state["share_token"]:
            raise AssertionError("无 share_token")
        r = requests.get(f"{BASE_URL}/api/shopping-list/shared/{state['share_token']}/")
        d = assertOK(r)
        cnt = len(d["data"]) if isinstance(d["data"], list) else d["data"].get("count", 0)
        print(f"    -> 分享清单条目数={cnt}")
    run("S-06", "查看分享的购物清单", s06)

    def s07():
        if not state["shopping_item_id"]:
            raise AssertionError("无购物项 id")
        r = delete(f"/api/shopping-list/{state['shopping_item_id']}/")
        assert r.status_code in (200, 204), f"HTTP {r.status_code}"
        print(f"    -> 购物项已删除")
    run("S-07", "删除购物项", s07)


# ══════════════════════════════════════════════════════════════
# 模块 5：Community（7 个）
# ══════════════════════════════════════════════════════════════

def test_module_community():
    sep("MODULE 5: COMMUNITY  (7 cases)")

    def c01():
        r = requests.get(f"{BASE_URL}/api/community/posts/")
        d = assertOK(r)
        cnt = d["data"].get("count", 0)
        print(f"    -> 动态总数={cnt}")
    run("C-01", "动态列表", c01)

    def c02():
        r = post("/api/community/posts/", json={
            "content": "这是一条测试动态，分享我的美食体验！西红柿炒蛋简单又好吃。",
            "images": []
        })
        d = assertOK(r)
        state["post_id"] = d["data"]["id"]
        print(f"    -> 发布动态 post_id={state['post_id']}")
    run("C-02", "发布动态", c02)

    def c03():
        if not state["post_id"]:
            raise AssertionError("无 post_id")
        r = requests.get(f"{BASE_URL}/api/community/posts/{state['post_id']}/")
        d = assertOK(r)
        print(f"    -> content前20字={d['data'].get('content','')[:20]}")
    run("C-03", "动态详情", c03)

    def c04():
        if not state["post_id"]:
            raise AssertionError("无 post_id")
        r = post(f"/api/community/posts/{state['post_id']}/like/")
        d = assertOK(r)
        print(f"    -> {d['message']}")
    run("C-04", "点赞动态", c04)

    def c05():
        if not state["post_id"]:
            raise AssertionError("无 post_id")
        r = post(f"/api/community/posts/{state['post_id']}/comments/", json={
            "content": "这道菜看起来很好吃！"
        })
        d = assertOK(r)
        state["comment_id"] = d["data"]["id"]
        print(f"    -> 评论成功 comment_id={state['comment_id']}")
    run("C-05", "发表评论", c05)

    def c06():
        if not state["post_id"]:
            raise AssertionError("无 post_id")
        r = requests.get(f"{BASE_URL}/api/community/posts/{state['post_id']}/comments/")
        d = assertOK(r)
        cnt = len(d["data"]) if isinstance(d["data"], list) else d["data"].get("count", 0)
        print(f"    -> 评论数={cnt}")
    run("C-06", "获取评论列表", c06)

    def c07():
        if not state["comment_id"]:
            raise AssertionError("无 comment_id")
        r = delete(f"/api/community/comments/{state['comment_id']}/")
        assert r.status_code in (200, 204), f"HTTP {r.status_code}"
        print(f"    -> 评论已删除")
    run("C-07", "删除评论", c07)


# ══════════════════════════════════════════════════════════════
# 模块 6：Nutrition（5 个）
# ══════════════════════════════════════════════════════════════

def test_module_nutrition():
    sep("MODULE 6: NUTRITION  (5 cases)")

    today = date.today().isoformat()

    def n01():
        r = post("/api/nutrition/diary/", json={
            "food_name": "西红柿炒蛋",
            "meal_type": "lunch",
            "calories": 320,
            "protein": 15.5,
            "fat": 12.0,
            "carbohydrate": 28.0,
            "fiber": 2.5,
            "date": today
        })
        d = assertOK(r)
        state["diary_id"] = d["data"]["id"]
        print(f"    -> 日记添加成功 diary_id={state['diary_id']}")
    run("N-01", "添加饮食日记", n01)

    def n02():
        r = get("/api/nutrition/diary/", params={"date": today})
        d = assertOK(r)
        cnt = len(d["data"]) if isinstance(d["data"], list) else d["data"].get("count", 0)
        print(f"    -> 今日日记条目数={cnt}")
    run("N-02", "获取饮食日记", n02)

    def n03():
        r = get("/api/nutrition/report/", params={"period": "week"})
        d = assertOK(r)
        print(f"    -> 周报生成成功, keys={list(d['data'].keys()) if isinstance(d['data'], dict) else 'list'}")
    run("N-03", "营养周报", n03)

    def n04():
        r = get("/api/nutrition/advice/")
        d = assertOK(r)
        print(f"    -> 健康建议已获取, keys={list(d['data'].keys()) if isinstance(d['data'], dict) else type(d['data']).__name__}")
    run("N-04", "健康建议", n04)

    def n05():
        if not state["recipe_id"]:
            raise AssertionError("无 recipe_id")
        r = requests.get(f"{BASE_URL}/api/nutrition/recipe/{state['recipe_id']}/")
        d = assertOK(r)
        print(f"    -> 食谱营养信息获取成功, keys={list(d['data'].keys()) if isinstance(d['data'], dict) else 'N/A'}")
    run("N-05", "食谱营养信息", n05)


# ══════════════════════════════════════════════════════════════
# 主程序
# ══════════════════════════════════════════════════════════════

def main():
    sep("智能食谱 API 完整测试  v2.0")
    print(f"  BASE_URL : {BASE_URL}")
    print(f"  测试用例  : 49 个（6 大模块）")
    print()

    # 检查服务器是否可达
    try:
        r = requests.get(f"{BASE_URL}/api/", timeout=5)
        print(f"  [OK] 服务器连接正常 (HTTP {r.status_code})")
    except Exception as e:
        print(f"  [ABORT] 无法连接服务器: {e}")
        print("  请先启动服务器: uv run python manage.py runserver")
        sys.exit(1)

    # 按模块执行
    test_module_user()
    test_module_ingredient()
    test_module_recipe()
    test_module_shopping()
    test_module_community()
    test_module_nutrition()

    # ── 汇总报告 ──────────────────────────────────────────────
    elapsed = time.time() - _start_time
    total = results["pass"] + results["fail"] + results["skip"]

    sep("TEST SUMMARY")
    print(f"  总用例  : {total}")
    print(f"  PASS   : {results['pass']}")
    print(f"  FAIL   : {results['fail']}")
    print(f"  SKIP   : {results['skip']}")
    print(f"  耗时    : {elapsed:.2f}s")
    print(f"  通过率  : {results['pass']}/{total - results['skip']} "
          f"({results['pass'] / max(total - results['skip'], 1) * 100:.1f}%)")

    print()
    if results["fail"]:
        print("  ── 失败用例 ──")
        for c in results["cases"]:
            if c["status"] in ("FAIL", "ERROR"):
                print(f"  [{c['id']}] {c['name']}: {c.get('error', '')}")

    print()
    print("  Tips:")
    print(f"    Access Token  到期: 30 分钟")
    print(f"    Refresh Token 到期: 7  天")
    print(f"    刷新端点: {BASE_URL}/api/user/token/refresh/")


if __name__ == "__main__":
    main()
