-- Pure Lua 5.1 harness. These mocks cannot prove WoW secure execution.
local tests, passed = {}, 0
local function equal(actual, expected)
    assert(actual == expected, tostring(actual) .. " ~= " .. tostring(expected))
end
local function world(saved, legacy, options)
    local w = { combat = false, bags = {}, auras = {}, frames = {}, messages = {},
        minimum = {}, requests = {}, writes = 0, scans = 0, level = 10, options = options or {} }
    local env = setmetatable({}, { __index = _G })
    w.env = env
    env.UIParent, env.SlashCmdList = {}, {}
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
            return "Localized item " .. id, nil, nil, nil, w.minimum[id] or 1
        end,
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
    assert(table.concat(w.messages, "\n"):find("1. Elixir of Minor Fortitude [ON]", 1, true))
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
for _, entry in ipairs(tests) do
    local ok, err = pcall(entry[2])
    if not ok then error("FAIL: " .. entry[1] .. ": " .. tostring(err)) end
    passed = passed + 1; print("PASS: " .. entry[1])
end
print("PASS: " .. passed .. " mocked scenarios; live client NOT VERIFIED")
