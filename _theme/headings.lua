-- Section numbers that authors write by hand ("## 1. A quick recap",
-- "## 2.1 Gates", "## Q1: Why ...") are set like the field guide's: in the
-- condensed face and muted, without the trailing "." or ":". The number is
-- wrapped in span.h-num, which the sidebar table of contents keeps too; the
-- space after it stays, so the text reads "Q1 Why ..." in search and feeds.
local NUMBER_PATTERNS = {
  "^(%d+)%.$",          -- 1.
  "^(%d+%.%d[%d%.]*)$", -- 2.1, 2.1.3
  "^(%d+%.%d[%d%.]*)%.$",
  "^(Q%d+):$",          -- Q1:
}

local function section_number(text)
  for _, pattern in ipairs(NUMBER_PATTERNS) do
    local number = text:match(pattern)
    if number then
      return number
    end
  end
  return nil
end

function Header(el)
  if el.level < 2 or el.level > 3 then
    return nil
  end
  local first, second = el.content[1], el.content[2]
  if first == nil or first.t ~= "Str" or second == nil or second.t ~= "Space" then
    return nil
  end
  local number = section_number(first.text)
  if number == nil then
    return nil
  end
  el.content[1] = pandoc.Span(pandoc.Inlines(number), pandoc.Attr("", { "h-num" }))
  return el
end
