-- Pure Lua 5.1 harness. These mocks cannot prove WoW secure execution.
local tests, passed = {}, 0
local function equal(actual, expected)
    assert(actual == expected, tostring(actual) .. " ~= " .. tostring(expected))
end
local function world(saved, legacy, options)
    local w = { combat = false, bags = {}, auras = {}, frames = {}, messages = {},
        minimum = {}, requests = {}, items = {}, slots = {}, writes = 0, scans = 0,
        level = 10, options = options or {} }
    local env = setmetatable({}, { __index = _G })
    w.env = env
    env.UIParent, env.SlashCmdList = {}, {}
    env.NUM_BAG_SLOTS = 4
    env.C_Container = {
        GetContainerNumSlots = function(bag)
            assert(not w.combat, "combat inventory inspection")
            assert(bag >= 0 and bag <= 4, "bank inspection")
            return #(w.slots[bag] or {})
        end,
        GetContainerItemID = function(bag, slot) return w.slots[bag][slot] end,
    }
    env.ForeverElixirManagerCharDB, env.ForeverElixirManagerDB = saved, legacy
    env.print = function(message) w.messages[#w.messages + 1] = message end
    env.InCombatLockdown = function() return w.combat end
    env.UnitLevel = function() return w.level end
    env.issecretvalue = function(v) return v == w.secret and w.secret ~= nil end
    env.C_Item = {
        GetItemCount = function(id, bank, uses, reagent, account)
            equal(bank, false); equal(uses, false); equal(reagent, false); equal(account, false)
            return w.bags[id] or 0
        end,
        GetItemInfo = function(id)
            if w.uncached == id then return nil end
            local item = w.items[id]
            if item then
                return item.name, nil, nil, nil, w.minimum[id] or 1,
                    nil, nil, nil, nil, nil, nil, item.class, item.subclass
            end
            return "Localized item " .. id, nil, nil, nil, w.minimum[id] or 1
        end,
        GetItemSpell = function(id) return w.items[id] and w.items[id].spell end,
        RequestLoadItemDataByID = function(id) w.requests[id] = (w.requests[id] or 0) + 1 end,
    }
    env.C_UnitAuras = { GetAuraDataByIndex = function(unit, index, filter)
        equal(unit, "player"); equal(filter, "HELPFUL")
        assert(not w.combat, "combat aura inspection")
        if index == 1 then w.scans = w.scans + 1 end
        if w.throwAura then error("unavailable") end
        return w.auras[index]
    end }
    env.CreateFrame = function(kind, name, parent, template)
        assert(not (name and w.combat), "protected frame created during combat")
        local f = { attributes = {}, scripts = {}, events = {} }
        function f:SetSize() end
        function f:SetPoint() end
        function f:SetAlpha() end
        function f:RegisterForClicks(phase) self.phase = phase end
        function f:SetAttribute(key, value)
            assert(not w.combat or w.secure, "insecure combat attribute write")
            if not w.secure then w.writes = w.writes + 1 end
            self.attributes[key] = value
        end
        function f:GetAttribute(key) return self.attributes[key] end
        function f:SetScript(key, fn) self.scripts[key] = fn end
        function f:GetScript(key) return self.scripts[key] end
        function f:RegisterEvent(event)
            if w.options.unsupportedEvent == event then error("unsupported event") end
            self.events[event] = true
        end
        w.frames[#w.frames + 1] = f
        if name then w.button = f; env[name] = f; w.template = template end
        return f
    end
    env.RegisterStateDriver = function(button, state, condition)
        equal(state, "combat"); equal(condition, "[combat] combat; safe")
        w.driver = assert(loadstring("return function(self, newstate) " ..
            button:GetAttribute("_onstate-combat") .. " end"))()
    end
    local chunk = assert(loadfile("ForeverElixirManager/ForeverElixirManager.lua"))
    setfenv(chunk, env); chunk()
    function w:event(event, unit, success)
        self.frames[1].scripts.OnEvent(self.frames[1], event, unit, success)
    end
    function w:flush()
        local fn = self.frames[1].scripts.OnUpdate
        if fn then fn(self.frames[1]) end
        equal(self.frames[1].scripts.OnUpdate, nil)
    end
    function w:command(text) self.env.SlashCmdList.FOREVERELIXIR(text) end
    function w:login() self:event("PLAYER_LOGIN") end
    function w:selected() return self.button and self.button.attributes.item end
    function w:carry(id, name, subclass, spell, bag)
        bag = bag or 0
        self.items[id] = { name = name, class = 0, subclass = subclass, spell = spell }
        self.bags[id] = 1
        self.slots[bag] = self.slots[bag] or {}
        table.insert(self.slots[bag], id)
    end
    function w:setCombat(value)
        self.combat, self.secure = value, true
        if self.driver then self.driver(self.button, value and "combat" or "safe") end
        self.secure = false
        if not value then self:event("PLAYER_REGEN_ENABLED") end
    end
    return w
end
local function test(name, fn) tests[#tests + 1] = {name, fn} end
test("startup events and slash before login", function()
    local w = world(); w:event("BAG_UPDATE"); w:event("UNIT_AURA", "player"); w:flush()
    w:command("list"); w:login(); equal(w:selected(), nil)
end)
test("fresh install queues without configuration", function()
    local w = world(); w.bags[2458] = 5; w:login(); equal(w:selected(), "item:2458")
end)
test("missing buff, localized names, item available", function()
    local w = world(); w.bags[2458] = 2; w:login()
    equal(w:selected(), "item:2458")
    equal(w.button.attributes.type, "item")
    equal(w.button.phase, "AnyUp"); equal(w.button.attributes.useOnKeyDown, false)
end)
test("active buff uses original English name", function()
    local w = world(); w.bags[2458] = 2; w.auras = {{name="Elixir of Minor Fortitude"}}
    w:login(); equal(w:selected(), nil)
end)
test("empty inventory and unavailable high priority", function()
    local w = world(); w:login(); equal(w:selected(), nil)
    w.bags[250330] = 1; w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), "item:250330")
end)
test("fixed priority and optional toggles", function()
    local w = world(); w.bags[2458], w.bags[250330] = 1, 1; w:login()
    equal(w:selected(), "item:2458")
    w:command("disable 1"); equal(w:selected(), "item:250330")
    w:command("enable 1"); equal(w:selected(), "item:2458")
    w:command("list"); w:command("buffs"); w:command("status")
    assert(table.concat(w.messages, "\n"):find("1. Fortitude [ON]", 1, true))
end)

test("client level requirements and level event", function()
    local w = world(); w.minimum[2458] = 11; w.bags[2458] = 1; w:login()
    equal(w:selected(), nil); w.level = 11; w:event("PLAYER_LEVEL_UP"); w:flush()
    equal(w:selected(), "item:2458")
end)
test("bag removal clears both secure attributes", function()
    local w = world(); w.bags[2458] = 1; w:login()
    w.bags[2458] = 0; w:event("BAG_UPDATE"); w:flush()
    equal(w:selected(), nil); equal(w.button.attributes.type, nil)
    equal(w.button.attributes.queuedType, nil)
end)
test("aura gain and loss refresh selection", function()
    local w = world(); w.bags[2458] = 1; w:login()
    w.auras = {{name="Elixir of Minor Fortitude"}}; w:event("UNIT_AURA", "player"); w:flush(); equal(w:selected(), nil)
    w.auras = {}; w:event("UNIT_AURA", "player"); w:flush(); equal(w:selected(), "item:2458")
end)
test("coalesces bag events, ignores other units, no redundant writes", function()
    local w = world(); w.bags[2458] = 1; w:login()
    local scans, writes = w.scans, w.writes
    w:event("UNIT_AURA", "target"); w:flush(); equal(w.scans, scans)
    for i=1,20 do w:event("BAG_UPDATE") end
    w:flush(); equal(w.scans, scans+1); equal(w.writes, writes)
end)
test("combat disables action, no insecure writes or scans, resume refreshes", function()
    local w = world(); w.bags[2458] = 1; w:login()
    local writes, scans = w.writes, w.scans
    w:setCombat(true); equal(w.button.attributes.type, nil)
    w.bags[2458] = 0; w:event("BAG_UPDATE"); w:event("UNIT_AURA", "player")
    w:command("status"); w:command("buffs"); w:command("disable 1"); w:flush()
    equal(w.writes, writes); equal(w.scans, scans)
    equal(w.env.ForeverElixirManagerCharDB.enabled[2458], true)
    w:setCombat(false); equal(w:selected(), nil)
end)
test("login during combat defers protected frame creation", function()
    local w = world(); w.combat = true; w:login(); equal(w.button, nil)
    w:setCombat(false); assert(w.button)
end)
test("toggles persist per character and old advanced settings are ignored", function()
    local legacy = {[2458]=false}
    local w = world(nil, legacy); w:login()
    equal(w.env.ForeverElixirManagerCharDB.enabled[2458], false)
    w:command("enable 1")
    local saved = w.env.ForeverElixirManagerCharDB
    saved.order, saved.auras, saved.blockers = {250330,2458}, {[2458]=9000}, {[2458]={[9000]=true}}
    local reloaded = world(saved, legacy)
    reloaded.bags[2458], reloaded.bags[250330] = 1, 1
    reloaded.auras = {{spellId=9000, name="Different buff"}}
    reloaded:login(); equal(reloaded:selected(), "item:2458")
    equal(saved.order[1],250330); equal(saved.auras[2458],9000)
    equal(saved.blockers[2458][9000],true)
    local other = world(nil, legacy); other:login()
    equal(other.env.ForeverElixirManagerCharDB.enabled[2458],false)
    equal(legacy[2458],false)
end)

test("malformed saved data and removed or invalid commands", function()
    for _, saved in ipairs({false, "bad", {enabled="bad"}}) do
        local w = world(saved); w.bags[2458] = 1; w:login()
        for _, cmd in ipairs({"move 1 2","disable 99","disable 1 extra","enable -1",
            "aura 1 1001","block 1 9000","unblock 1 9000","reset"}) do w:command(cmd) end
        equal(w:selected(),"item:2458")
        equal(w.env.ForeverElixirManagerCharDB.enabled[2458],true)
    end
end)

test("uncached item requests once and refreshes on receipt", function()
    local w = world(); w.bags[2458] = 1; w.uncached = 2458; w:login()
    equal(w:selected(),nil); equal(w.requests[2458],1)
    w:command("status"); equal(w.requests[2458],1)
    w.uncached = nil; w:event("GET_ITEM_INFO_RECEIVED",2458); w:flush()
    equal(w:selected(),"item:2458")
end)
test("invalid API values, missing APIs and thrown errors clear selection", function()
    for _, fault in ipairs({"count","level","aura","missing","throw","secret"}) do
        local w = world(); w.bags[2458]=1; w:login()
        if fault=="count" then w.bags[2458]="bad"
        elseif fault=="level" then w.level=-1
        elseif fault=="aura" then w.auras={{spellId=1001}}
        elseif fault=="missing" then w.env.C_Item={}
        elseif fault=="throw" then w.throwAura=true
        else w.secret={}; w.auras={{name=w.secret}} end
        w:event("BAG_UPDATE"); w:flush(); equal(w:selected(),nil)
    end
end)
test("failed item load does not cause request or event retry loop", function()
    local w = world(); w.bags[2458] = 1; w.uncached = 2458; w:login()
    w:event("GET_ITEM_INFO_RECEIVED",2458,false); w:flush()
    w.env.C_Item.GetItemInfo = function() error("must not repeat a failed lookup") end
    w:event("BAG_UPDATE"); w:flush(); equal(w.requests[2458],1)
    equal(w:selected(),nil)
end)
test("missing secure API or unsupported event leaves action unarmed", function()
    local w = world(); w.env.RegisterStateDriver=false; w:login(); equal(w.button,nil)
    w = world(nil,nil,{unsupportedEvent="UNIT_AURA"}); w:login(); equal(w.button,nil)
    w = world(); w.env.InCombatLockdown=false; w:login(); equal(w.button,nil)
end)
test("all six groups choose their strongest carried rank", function()
    for _, pair in ipairs({{2458,250335},{250330,250333},{250339,250341},
        {250344,250347},{3383,9179},{3389,13445}}) do
        local w = world(); w.level = 60; w.bags[pair[1]], w.bags[pair[2]] = 1, 1
        w:login(); equal(w:selected(), "item:" .. pair[2])
    end
end)

test("rank fallback follows bag removals and client level limits", function()
    local w = world(); w.level = 54
    w.bags[250335], w.bags[250334], w.bags[3825], w.bags[2458] = 1, 1, 1, 1
    w.minimum[250335], w.minimum[250334], w.minimum[3825], w.minimum[2458] = 55, 45, 25, 2
    w:login(); equal(w:selected(), "item:250334")
    w.bags[250334] = 0; w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), "item:3825")
    w.level = 24; w:event("PLAYER_LEVEL_UP"); w:flush(); equal(w:selected(), "item:2458")
    w.level = 55; w:event("PLAYER_LEVEL_UP"); w:flush(); equal(w:selected(), "item:250335")
    w.bags[250335], w.bags[3825], w.bags[2458] = 0, 0, 0
    w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), nil)
end)

test("recognized stronger buff blocks all lower ranks even without its item", function()
    for _, entry in ipairs({{2458,"Elixir of Greater Fortitude"},
        {250330,"Greater Cleric's Elixir"},{250339,"Greater Mageblood Elixir"},
        {250344,"Elixir of Greater Spirit"},{3383,"Elixir of Greater Intellect"},
        {3389,"Elixir of Greater Defense"}}) do
        local w = world(); w.bags[entry[1]] = 1; w.auras = {{name=entry[2]}}
        w:login(); equal(w:selected(), nil)
    end
end)

test("weaker buff permits manual upgrade but equal buff prevents reuse", function()
    local w = world(); w.bags[2458], w.bags[3825] = 1, 1
    w.auras = {{name="Elixir of Minor Fortitude"}}
    w:login(); equal(w:selected(), "item:3825")
    w.auras = {{name="Elixir of Lesser Fortitude"}}
    w:event("UNIT_AURA","player"); w:flush(); equal(w:selected(), nil)
    w.auras = {}; w:event("UNIT_AURA","player"); w:flush(); equal(w:selected(), "item:3825")
end)

test("equal intellect effects neither replace each other nor hide upgrades", function()
    local w = world(); w.bags[3383], w.bags[250353] = 1, 1
    w:login(); equal(w:selected(), "item:3383")
    w.bags[3383] = 0; w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), "item:250353")
    w.auras = {{name="Elixir of Wisdom"}}
    w:event("UNIT_AURA","player"); w:flush(); equal(w:selected(), nil)
    w.bags[9179] = 1; w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), "item:9179")
end)

test("effect strength wins over item naming and required level", function()
    local w = world(); w.level = 45
    w.bags[9179], w.bags[250354], w.bags[3383] = 1, 1, 1
    w.minimum[9179], w.minimum[250354] = 37, 45
    w:login(); equal(w:selected(), "item:9179")
    w.bags[9179] = 0; w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), "item:250354")
end)

test("existing disabled toggles cover every rank and survive reload", function()
    local legacy = {[2458]=false}
    local w = world(nil, legacy); w.bags[250335] = 1; w:login(); equal(w:selected(), nil)
    w:command("enable 1"); equal(w:selected(), "item:250335")
    w:command("disable 1"); equal(w:selected(), nil)
    local reloaded = world(w.env.ForeverElixirManagerCharDB, legacy)
    reloaded.bags[250335] = 1; reloaded:login(); equal(reloaded:selected(), nil)
end)

test("uncached stronger item falls back then upgrades after data arrives", function()
    local w = world(); w.bags[250335], w.bags[2458] = 1, 1; w.uncached = 250335
    w:login(); equal(w:selected(), "item:2458"); equal(w.requests[250335], 1)
    w.uncached = nil; w:event("GET_ITEM_INFO_RECEIVED",250335,true); w:flush()
    equal(w:selected(), "item:250335")
end)

test("rank changes pause in combat and resume without insecure combat writes", function()
    local w = world(); w.bags[2458] = 1; w:login(); w:setCombat(true)
    local writes, scans = w.writes, w.scans
    w.bags[250335] = 1; w:event("BAG_UPDATE"); w:flush()
    equal(w:selected(), "item:2458"); equal(w.button.attributes.type, nil)
    equal(w.writes, writes); equal(w.scans, scans)
    w:setCombat(false); equal(w:selected(), "item:250335")
end)

test("group order is retained when later groups have stronger ranks", function()
    local w = world(); w.bags[2458], w.bags[250333] = 1, 1
    w:login(); equal(w:selected(), "item:2458")
    w:command("disable 1"); equal(w:selected(), "item:250333")
end)

test("reported Minor Strength is discovered and its use-name buff prevents reuse", function()
    local w = world(); w:carry(2454, "Elixir of Minor Strength", 2, "Lesser Strength")
    w:login(); equal(w:selected(), "item:2454")
    w.auras = {{name="Lesser Strength"}}
    w:event("UNIT_AURA", "player"); w:flush(); equal(w:selected(), nil)
    w.auras = {}; w:event("UNIT_AURA", "player"); w:flush()
    equal(w:selected(), "item:2454")
end)

test("all client-classified elixirs and scrolls including unknown IDs are discovered", function()
    for _, subclass in ipairs({2, 4}) do
        local w = world(); w:carry(900001, "Localized consumable", subclass, "Localized effect", 4)
        w:login(); equal(w:selected(), "item:900001")
        w.auras = {{name="Localized effect"}}; w:event("UNIT_AURA", "player"); w:flush()
        equal(w:selected(), nil)
    end
end)

test("scrolls explicitly target the player and all matching ranks stop on an active name", function()
    local w = world(); w:carry(954, "Scroll of Strength", 4, "Strength")
    w:carry(2289, "Scroll of Strength II", 4, "Strength")
    w:login(); equal(w:selected(), "item:954"); equal(w.button.attributes.unit, "player")
    w.auras = {{name="Strength"}}; w:event("UNIT_AURA", "player"); w:flush()
    equal(w:selected(), nil)
end)

test("discovery excludes other categories even when their names say elixir or scroll", function()
    for _, class in ipairs({0, 9, 12}) do
        for _, subclass in ipairs({0, 1, 2, 3, 4, 5, 6, 7, 8}) do
            if class ~= 0 or (subclass ~= 2 and subclass ~= 4) then
                local w = world(); w:carry(900001, "Elixir scroll recipe", subclass, "Effect")
                w.items[900001].class = class; w:login(); equal(w:selected(), nil)
            end
        end
    end
end)

test("discovery uses equipped bags only and clears a banked or removed item", function()
    local w = world(); w:carry(2454, "Minor Strength", 2, "Lesser Strength", 4)
    w:login(); equal(w:selected(), "item:2454")
    w.slots[4], w.slots[5] = {}, {2454}
    w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), nil)
    equal(w.button.attributes.type, nil)
end)

test("discovery respects level, deduplicates stacks and keeps order across bag moves", function()
    local w = world(); w:carry(900002, "Second", 2, "Effect B")
    w:carry(900001, "First", 2, "Effect A"); w.slots[1] = {900001}
    w.minimum[900001] = 11; w:login(); equal(w:selected(), "item:900002")
    w.level = 11; w:event("PLAYER_LEVEL_UP"); w:flush(); equal(w:selected(), "item:900001")
    w.slots[0] = {900001, 900002}; w.slots[1] = {}
    w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), "item:900001")
    w:command("list")
    local count = 0
    for _, message in ipairs(w.messages) do
        if message:find("First (item 900001", 1, true) then count = count + 1 end
    end
    equal(count, 1)
end)

test("known groups retain priority and disabled ranked items cannot reenter through discovery", function()
    local w = world(); w:carry(2458, "Elixir of Minor Fortitude", 2, "Fortitude")
    w:carry(2454, "Minor Strength", 2, "Lesser Strength")
    w:carry(954, "Scroll of Strength", 4, "Strength")
    w:login(); equal(w:selected(), "item:2458")
    w:command("disable 1"); equal(w:selected(), "item:2454")
    w:command("disable 7"); equal(w:selected(), "item:954")
    w:command("disable 8"); equal(w:selected(), nil)
    w:command("enable 7"); equal(w:selected(), "item:2454")
    local reloaded = world(w.env.ForeverElixirManagerCharDB)
    reloaded:carry(954, "Scroll of Strength", 4, "Strength")
    reloaded:login(); equal(reloaded:selected(), nil)
    reloaded:command("enable 8"); equal(reloaded:selected(), "item:954")
end)

test("existing per-character settings enable new categories without overwriting old choices", function()
    local saved = {enabled = {[2458]=false}}
    local w = world(saved); w:carry(2454, "Minor Strength", 2, "Lesser Strength")
    w:login(); equal(w:selected(), "item:2454"); equal(saved.enabled[2458], false)
end)

test("uncached discovery retries on item-data receipt and failed loads do not loop", function()
    for _, success in ipairs({true, false}) do
        local w = world(); w:carry(2454, "Minor Strength", 2, "Lesser Strength")
        w.uncached = 2454; w:login(); equal(w:selected(), nil); equal(w.requests[2454], 1)
        w:command("status"); equal(w.requests[2454], 1)
        w.uncached = nil; w:event("GET_ITEM_INFO_RECEIVED", 2454, success); w:flush()
        equal(w:selected(), success and "item:2454" or nil)
        w:event("BAG_UPDATE"); w:flush(); equal(w.requests[2454], 1)
    end
end)

test("missing use spell is reported and never queues an unidentified effect", function()
    local w = world(); w:carry(2454, "Minor Strength", 2)
    w:login(); equal(w:selected(), nil)
    assert(table.concat(w.messages, "\n"):find("discovery incomplete", 1, true))
    w.items[2454].spell = "Lesser Strength"
    w:event("GET_ITEM_INFO_RECEIVED", 2454, true); w:flush(); equal(w:selected(), "item:2454")
    w:command("buffs")
    assert(table.concat(w.messages, "\n"):find("assumed buff: Lesser Strength", 1, true))
end)

test("discovered items recognize item labels without equating use spell IDs and aura IDs", function()
    local w = world(); w:carry(2454, "Minor Strength", 2, "Lesser Strength")
    w.auras = {{name="Minor Strength"}}; w:login(); equal(w:selected(), nil)
    w.auras = {{name="Unrelated effect", spellId=2367}}
    w:event("UNIT_AURA", "player"); w:flush(); equal(w:selected(), "item:2454")
end)

test("missing discovery APIs report the limitation while preserving known group support", function()
    local w = world(); w.env.C_Container = nil; w:login(); equal(w:selected(), nil)
    assert(table.concat(w.messages, "\n"):find("Bag discovery API unavailable", 1, true))
    w.bags[2458] = 1; w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), "item:2458")
end)

test("unreadable discovery clears selection and never selects a different item category", function()
    for _, field in ipairs({"class", "subclass", "spell", "name"}) do
        local w = world(); w:carry(2454, "Minor Strength", 2, "Lesser Strength"); w:login()
        w.secret = {}; w.items[2454][field] = w.secret
        w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), nil)
    end
end)

test("discovery, commands and bag changes make no decisions or protected writes in combat", function()
    local w = world(); w:carry(2454, "Minor Strength", 2, "Lesser Strength"); w:login()
    w:setCombat(true); local writes, scans = w.writes, w.scans
    w.slots[0], w.bags[2454] = {}, 0
    w:carry(954, "Scroll of Strength", 4, "Strength")
    w:event("BAG_UPDATE"); w:command("list"); w:command("buffs"); w:command("disable 8"); w:flush()
    equal(w.writes, writes); equal(w.scans, scans); equal(w.button.attributes.type, nil)
    w:setCombat(false); equal(w:selected(), "item:954")
end)

for _, entry in ipairs(tests) do
    local ok, err = pcall(entry[2])
    if not ok then error("FAIL: " .. entry[1] .. ": " .. tostring(err)) end
    passed = passed + 1; print("PASS: " .. entry[1])
end
print("PASS: " .. passed .. " mocked scenarios; live client NOT VERIFIED")
