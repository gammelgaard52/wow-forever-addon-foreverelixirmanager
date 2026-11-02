-- Pure Lua 5.1 harness. These mocks cannot prove WoW secure execution.
local tests, passed = {}, 0
local ids = {2458, 250330, 250339, 250344, 3383, 3389}
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
    env.C_Spell = { GetSpellInfo = function(id)
        if w.invalidSpell == id then return nil end
        return { spellID = id }
    end }
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
    function w:mapAll()
        for i in ipairs(ids) do self:command("aura " .. i .. " " .. (1000 + i)) end
    end
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
test("unverified mappings do not queue", function()
    local w = world(); w.bags[2458] = 5; w:login(); equal(w:selected(), nil)
end)
test("missing buff, localized names, item available", function()
    local w = world(); w.bags[2458] = 2; w:login(); w:mapAll()
    equal(w:selected(), "item:2458")
    equal(w.button.attributes.type, "item")
    equal(w.button.phase, "AnyUp"); equal(w.button.attributes.useOnKeyDown, false)
end)
test("active aura uses spell ID, not item name", function()
    local w = world(); w.bags[2458] = 2; w.auras = {{spellId=1001, name="Different name"}}
    w:login(); w:mapAll(); equal(w:selected(), nil)
end)
test("empty inventory and unavailable high priority", function()
    local w = world(); w:login(); w:mapAll(); equal(w:selected(), nil)
    w.bags[250330] = 1; w:event("BAG_UPDATE"); w:flush(); equal(w:selected(), "item:250330")
end)
test("deterministic priority and move command", function()
    local w = world(); w.bags[2458], w.bags[250330] = 1, 1; w:login(); w:mapAll()
    equal(w:selected(), "item:2458"); w:command("move 2 1"); equal(w:selected(), "item:250330")
    w:command("disable 1"); equal(w:selected(), "item:2458")
    w:command("enable 1"); equal(w:selected(), "item:250330")
end)
test("client level requirements and level event", function()
    local w = world(); w.minimum[2458] = 11; w.bags[2458] = 1; w:login(); w:mapAll()
    equal(w:selected(), nil); w.level = 11; w:event("PLAYER_LEVEL_UP"); w:flush()
    equal(w:selected(), "item:2458")
end)
test("configured higher rank or conflicting aura blocks", function()
    local w = world(); w.bags[2458] = 1; w.auras = {{spellId=9000}}
    w:login(); w:mapAll(); w:command("block 1 9000"); equal(w:selected(), nil)
    w:command("unblock 1 9000"); equal(w:selected(), "item:2458")
end)
test("bag removal clears both secure attributes", function()
    local w = world(); w.bags[2458] = 1; w:login(); w:mapAll()
    w.bags[2458] = 0; w:event("BAG_UPDATE"); w:flush()
    equal(w:selected(), nil); equal(w.button.attributes.type, nil)
    equal(w.button.attributes.queuedType, nil)
end)
test("aura gain and loss refresh selection", function()
    local w = world(); w.bags[2458] = 1; w:login(); w:mapAll()
    w.auras = {{spellId=1001}}; w:event("UNIT_AURA", "player"); w:flush(); equal(w:selected(), nil)
    w.auras = {}; w:event("UNIT_AURA", "player"); w:flush(); equal(w:selected(), "item:2458")
end)
test("coalesces bag events, ignores other units, no redundant writes", function()
    local w = world(); w.bags[2458] = 1; w:login(); w:mapAll()
    local scans, writes = w.scans, w.writes
    w:event("UNIT_AURA", "target"); w:flush(); equal(w.scans, scans)
    for i=1,20 do w:event("BAG_UPDATE") end
    w:flush(); equal(w.scans, scans+1); equal(w.writes, writes)
end)
test("combat disables action, no insecure writes or scans, resume refreshes", function()
    local w = world(); w.bags[2458] = 1; w:login(); w:mapAll()
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
test("saved configuration migrates and remains per character", function()
    local legacy = {[2458]=false}
    local w = world(nil, legacy); w:login(); w:mapAll(); w:command("move 2 1"); w:command("block 1 9000")
    local saved = w.env.ForeverElixirManagerCharDB
    local reloaded = world(saved, legacy); reloaded:login()
    equal(reloaded.env.ForeverElixirManagerCharDB.order[1],250330)
    equal(reloaded.env.ForeverElixirManagerCharDB.auras[2458],1001)
    equal(reloaded.env.ForeverElixirManagerCharDB.blockers[250330][9000],true)
    local other = world(nil, legacy); other:login()
    equal(other.env.ForeverElixirManagerCharDB.auras[2458],nil)
    reloaded:command("reset"); equal(reloaded.env.ForeverElixirManagerCharDB.enabled[2458],true)
    equal(legacy[2458],false)
end)
test("malformed saved data and invalid commands", function()
    local w = world({order={2458,2458,999},enabled="bad",auras={[2458]=-1},blockers="bad"})
    w:login(); equal(#w.env.ForeverElixirManagerCharDB.order,6)
    for _, cmd in ipairs({"move 1 99","disable 99","aura 1 -2","aura 1 nope","reset extra"}) do w:command(cmd) end
    equal(w:selected(),nil)
end)
test("uncached item requests once and refreshes on receipt", function()
    local w = world(); w.bags[2458] = 1; w.uncached = 2458; w:login(); w:mapAll()
    equal(w:selected(),nil); equal(w.requests[2458],1)
    w:command("status"); equal(w.requests[2458],1)
    w.uncached = nil; w:event("GET_ITEM_INFO_RECEIVED",2458); w:flush()
    equal(w:selected(),"item:2458")
end)
test("invalid API values, missing APIs and thrown errors clear selection", function()
    for _, fault in ipairs({"count","level","spell","aura","missing","throw","secret"}) do
        local w = world(); w.bags[2458]=1; w:login(); w:mapAll()
        if fault=="count" then w.bags[2458]="bad"
        elseif fault=="level" then w.level=-1
        elseif fault=="spell" then w.invalidSpell=1001
        elseif fault=="aura" then w.auras={{name="No ID"}}
        elseif fault=="missing" then w.env.C_Item={}
        elseif fault=="throw" then w.throwAura=true
        else w.secret={}; w.auras={{spellId=w.secret}} end
        w:event("BAG_UPDATE"); w:flush(); equal(w:selected(),nil)
    end
end)
test("failed item load does not cause request or event retry loop", function()
    local w = world(); w.bags[2458] = 1; w.uncached = 2458; w:login(); w:mapAll()
    w:event("GET_ITEM_INFO_RECEIVED",2458,false); w:flush()
    w.env.C_Item.GetItemInfo = function() error("must not repeat a failed lookup") end
    w:event("BAG_UPDATE"); w:flush(); equal(w.requests[2458],1)
    equal(w:selected(),nil)
    w:command("list")
    assert(table.concat(w.messages,"\n"):find("item data request failed",1,true))
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
