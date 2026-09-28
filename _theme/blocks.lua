-- Markup for the field guide's code and table cards (styled in theme.scss):
--   - a code block with a language gets data-lang, shown as the uppercase
--     label in the block's header strip;
--   - a Markdown table is wrapped in div.table-wrap, the bordered card that
--     scrolls sideways on small screens. Cross-referenced tables (#tbl-...)
--     are left to Quarto's float layout.
local LANGUAGE_LABELS = {
  python = "Python",
  py = "Python",
  ipython = "Python",
  ipython3 = "Python",
  bash = "Shell",
  sh = "Shell",
  shell = "Shell",
  zsh = "Shell",
  console = "Shell",
  powershell = "PowerShell",
  toml = "TOML",
  yaml = "YAML",
  json = "JSON",
  sql = "SQL",
  html = "HTML",
  css = "CSS",
  javascript = "JavaScript",
  js = "JavaScript",
  typescript = "TypeScript",
  postscript = "PostScript",
  dockerfile = "Dockerfile",
  markdown = "Markdown",
  r = "R",
}

-- Classes that mark a code block without being its language.
local NOT_LANGUAGES = {
  ["cell-code"] = true,
  ["code-overflow-wrap"] = true,
  ["code-overflow-scroll"] = true,
  ["hidden"] = true,
  ["text"] = true,
  ["plaintext"] = true,
}

local function language(el)
  for _, class in ipairs(el.classes) do
    if not NOT_LANGUAGES[class] and not class:match("^code%-") then
      return class
    end
  end
  return nil
end

function CodeBlock(el)
  if el.attributes["data-lang"] ~= nil then
    return nil
  end
  local lang = language(el)
  if lang == nil then
    return nil
  end
  el.attributes["data-lang"] = LANGUAGE_LABELS[lang:lower()] or lang
  return el
end

function Table(el)
  if el.identifier ~= nil and el.identifier:match("^tbl%-") then
    return nil
  end
  return pandoc.Div({ el }, pandoc.Attr("", { "table-wrap" }))
end
