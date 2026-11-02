-- Copyright (c) 2026 Martin Gammelgård Rasmussen. MIT; see packaged LICENSE.
-- Original fixed priority and English buff-name assumptions; see docs/VALIDATION.md.
local PREFIX = "|cff8bcaff[ElixirManager]|r "
local elixirs = {
    { id = 2458, name = "Elixir of Minor Fortitude" },
    { id = 250330, name = "Minor Cleric's Elixir" },
    { id = 250339, name = "Minor Mageblood Elixir" },
    { id = 250344, name = "Elixir of Minor Spirit" },
    { id = 3383, name = "Elixir of Wisdom" },
    { id = 3389, name = "Elixir of Lesser Defense" },
}
local frame = CreateFrame("Frame")
local button, settings, queuedID, lastMessage, startupError
local pendingItems = {}
local function say(message) print(PREFIX .. message) end
local function report(message)
    if message ~= lastMessage then say(message); lastMessage = message end
end
local function readable(value)
    return not issecretvalue or not issecretvalue(value)
end
local function integer(value, minimum)
    return readable(value) and type(value) == "number" and value < math.huge
        and value >= minimum and value == math.floor(value)
end
local function locked()
    return type(InCombatLockdown) ~= "function" or InCombatLockdown()
end
local function activeAuras()
    if not C_UnitAuras or type(C_UnitAuras.GetAuraDataByIndex) ~= "function" then
        return nil, "Aura API unavailable; selection stopped."
    end
    local active = {}
    for i = 1, 255 do
        local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
        if not readable(aura) then return nil, "Restricted aura data; selection stopped." end
        if aura == nil then return active end
        if type(aura) ~= "table" or not readable(aura.name) or type(aura.name) ~= "string"
            or aura.name == "" then
            return nil, "Unreadable buff name; selection stopped."
        end
        active[aura.name] = true
    end
    return nil, "Aura scan limit reached; selection stopped."
end
local function candidate(entry, level, active)
    local id = entry.id
    if settings[id] == false or active[entry.name] then return end
    local count = C_Item.GetItemCount(id, false, false, false, false)
    if not integer(count, 1) or pendingItems[id] == "failed" then return end
    local name, _, _, _, minimum = C_Item.GetItemInfo(id)
    if not readable(name) or type(name) ~= "string" or not integer(minimum, 0) then
        if not pendingItems[id] and type(C_Item.RequestLoadItemDataByID) == "function" then
            pendingItems[id] = true
            C_Item.RequestLoadItemDataByID(id)
        end
        return
    end
    if level >= minimum then return name end
end
local function selectItem()
    if not C_Item or type(C_Item.GetItemCount) ~= "function" or type(C_Item.GetItemInfo) ~= "function"
        or type(UnitLevel) ~= "function" then return nil, "Required item/level API unavailable." end
    local level = UnitLevel("player")
    if not integer(level, 1) then return nil, "Player level unavailable." end
    local active, detail = activeAuras()
    if not active then return nil, detail end
    for _, entry in ipairs(elixirs) do
        local name = candidate(entry, level, active)
        if name then return entry.id, "Next up: " .. name end
    end
    return nil, "No missing enabled elixir available for your level."
end
local function applySelection(id)
    if queuedID == id then return end
    -- Disable before changing the target. Item IDs survive bag-slot moves.
    button:SetAttribute("type", nil)
    button:SetAttribute("item", id and ("item:" .. id) or nil)
    button:SetAttribute("queuedType", id and "item" or nil)
    button:SetAttribute("type", id and "item" or nil)
    queuedID = id
end
local function update()
    if not settings then return end
    if startupError then report(startupError); return end
    if not button then return end
    if locked() then return end -- No aura/inventory decisions in combat.
    local ok, id, message = pcall(selectItem)
    if not ok then id, message = nil, "Client API error; selection stopped. Use /fem status." end
    applySelection(id)
    report(message)
end
local function initializeButton()
    if type(InCombatLockdown) ~= "function" then
        startupError = "Combat API unavailable; manual queue disabled."
        return
    end
    if locked() then return end
    if type(RegisterStateDriver) ~= "function" then
        startupError = "Secure state API unavailable; manual queue disabled."
        return
    end
    button = CreateFrame("Button", "ForeverElixirSecureBtn", UIParent,
        "SecureActionButtonTemplate,SecureHandlerStateTemplate")
    button:SetSize(1, 1)
    button:SetPoint("TOPLEFT", UIParent, "TOPLEFT", -10, 10)
    button:SetAlpha(0)
    button:RegisterForClicks("AnyUp")
    button:SetAttribute("useOnKeyDown", false)
    -- Fixed combat condition only: no item selection or combat decisions here.
    button:SetAttribute("_onstate-combat", [[
        if newstate == "combat" then
            self:SetAttribute("type", nil)
        else
            self:SetAttribute("type", self:GetAttribute("queuedType"))
        end
    ]])
    RegisterStateDriver(button, "combat", "[combat] combat; safe")
end
local function initialize()
    if not settings then
        if type(ForeverElixirManagerCharDB) ~= "table" then ForeverElixirManagerCharDB = {} end
        local db = ForeverElixirManagerCharDB
        if type(db.enabled) ~= "table" then
            db.enabled = {}
            for _, entry in ipairs(elixirs) do
                db.enabled[entry.id] = type(ForeverElixirManagerDB) ~= "table"
                    or ForeverElixirManagerDB[entry.id] ~= false
            end
        end
        settings = db.enabled
        -- Old order/mappings/blockers are ignored but retained for rollback.
    end
    if not button and not startupError then
        local ok = pcall(initializeButton)
        if not ok then startupError = "Secure button setup failed; reload after checking client support." end
    end
    if button or startupError then update() end
end
local function schedule()
    if not settings or locked() or frame:GetScript("OnUpdate") then return end
    -- One next-frame refresh per event burst; no permanent polling.
    frame:SetScript("OnUpdate", function(self)
        self:SetScript("OnUpdate", nil)
        update()
    end)
end
frame:SetScript("OnEvent", function(_, event, unit, success)
    if event == "PLAYER_LOGIN" or event == "PLAYER_REGEN_ENABLED" then initialize(); return end
    if event == "UNIT_AURA" and unit ~= "player" then return end
    if event == "GET_ITEM_INFO_RECEIVED" then
        if not pendingItems[unit] then return end
        if success == false then pendingItems[unit] = "failed"
        elseif success == true then pendingItems[unit] = true end
    end
    schedule()
end)
for _, event in ipairs({ "PLAYER_LOGIN", "PLAYER_REGEN_ENABLED", "PLAYER_ENTERING_WORLD",
    "BAG_UPDATE", "UNIT_AURA", "PLAYER_LEVEL_UP", "GET_ITEM_INFO_RECEIVED" }) do
    local ok = pcall(frame.RegisterEvent, frame, event)
    if not ok then startupError = "Required event unavailable: " .. event .. "; selection stopped." end
end
SLASH_FOREVERELIXIR1 = "/fem"
SlashCmdList.FOREVERELIXIR = function(arg)
    if not settings then say("Waiting for player login."); return end
    arg = (arg or ""):lower():match("^%s*(.-)%s*$")
    local command, number = arg:match("^(%S+)%s+(%d+)$")
    local entry = elixirs[tonumber(number)]
    if arg == "status" then
        if locked() then say("Combat: selection paused; secure item action disabled.")
        else update(); say(lastMessage or "No item queued.") end
    elseif arg == "list" then
        for index, item in ipairs(elixirs) do
            say(index .. ". " .. item.name .. " [" .. (settings[item.id] == false and "OFF" or "ON") .. "]")
        end
    elseif arg == "buffs" then
        if locked() then say("Aura inspection unavailable in combat."); return end
        local ok, active = pcall(activeAuras)
        if not ok or not active then say("Aura data unavailable."); return end
        for _, item in ipairs(elixirs) do
            say(item.name .. ": " .. (active[item.name] and "ACTIVE" or "MISSING"))
        end
    elseif (command == "enable" or command == "disable") and entry then
        if locked() then say("Configuration unavailable in combat."); return end
        settings[entry.id] = command == "enable"
        update()
        say(entry.name .. (command == "enable" and " enabled." or " disabled."))
    else
        update()
        say("Commands: /fem list, /fem enable N, /fem disable N, /fem buffs, /fem status")
    end
end
