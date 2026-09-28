-- Interactive charts in the style of the Jev Field Guide.
--
--   {{< chart name >}}
--
-- Reads assets/charts/<name>.json next to the post, written by
-- `uv run figkit build` from the post's figures.py (tools/figkit/charts.py),
-- and emits the chart card: kicker, title, subtitle, legend, the chart box
-- that chartkit.js draws into, a "Show the numbers" table and the source.
-- Everything except the drawing is plain HTML, so the title, the table and
-- the source are there without JavaScript, in search and in feeds.
--
-- A post with custom widgets keeps them in posts/<slug>/charts.js
-- (Chartkit.register("name", draw)); it is loaded once per page.

local post_script_added = false

local function stringify_arg(value)
  if value == nil then
    return nil
  end
  local text = pandoc.utils.stringify(value)
  if text == "" then
    return nil
  end
  return text
end

local function escape(text)
  return (tostring(text):gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
end

local function post_dir()
  return pandoc.path.directory(quarto.doc.input_file)
end

local function load_spec(name)
  local path = pandoc.path.join({ post_dir(), "assets", "charts", name .. ".json" })
  local file = io.open(path, "r")
  if file == nil then
    error("chartkit: no chart spec at " .. path .. " (run `uv run figkit build`)")
  end
  local spec = quarto.json.decode(file:read("a"))
  file:close()
  return spec
end

-- Markdown text as a Div of inline content (no paragraph margins).
local function markdown_div(text, class, id)
  if text == nil or text == "" then
    return nil
  end
  local blocks = pandoc.read(text, "markdown").blocks
  local inlines = pandoc.Inlines({})
  for index, block in ipairs(blocks) do
    if index > 1 then
      inlines:insert(pandoc.Space())
    end
    if block.content then
      inlines:extend(block.content)
    end
  end
  return pandoc.Div({ pandoc.Plain(inlines) }, pandoc.Attr(id or "", { class }))
end

local SWATCH_COLORS = { ["1"] = "c1", ["2"] = "c2", ["3"] = "c3", person = "cp", p = "cp" }

local function legend(spec)
  if spec.legend == nil or #spec.legend == 0 then
    return nil
  end
  local parts = {}
  for _, item in ipairs(spec.legend) do
    local color = SWATCH_COLORS[tostring(item.color or 1)] or "c1"
    local kind = item.kind or "line"
    local classes = color
    if kind == "dot" then
      classes = "dot " .. color
    elseif kind == "dash" then
      classes = "dash " .. color
    end
    table.insert(parts, string.format('<span><i class="%s" aria-hidden="true"></i>%s</span>', classes, escape(item.name)))
  end
  return pandoc.RawBlock("html", '<div class="w-legend">' .. table.concat(parts) .. "</div>")
end

local function data_table(spec)
  local t = spec.table
  if t == nil or t.columns == nil or t.rows == nil then
    return nil
  end
  local numeric = t.numeric or {}
  local function cell(tag, value, index)
    local class = ""
    if numeric[index] then
      class = ' class="num"'
    end
    return string.format("<%s%s>%s</%s>", tag, class, escape(value), tag)
  end
  local head = {}
  for index, column in ipairs(t.columns) do
    table.insert(head, cell("th", column, index))
  end
  local rows = {}
  for _, row in ipairs(t.rows) do
    local cells = {}
    for index, value in ipairs(row) do
      table.insert(cells, cell("td", value, index))
    end
    table.insert(rows, "<tr>" .. table.concat(cells) .. "</tr>")
  end
  return pandoc.RawBlock("html", string.format(
    '<details class="w-data"><summary>%s</summary><div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div></details>',
    escape(t.summary or "Show the numbers"), table.concat(head), table.concat(rows)))
end

-- The part of the spec chartkit.js needs to draw (the rest is HTML above).
local DRAW_ONLY = { title = true, sub = true, kicker = true, source = true, table = true, legend = true, version = true }

local function drawing_spec(spec)
  local out = {}
  for key, value in pairs(spec) do
    if not DRAW_ONLY[key] then
      out[key] = value
    end
  end
  return out
end

local function chart(args, kwargs)
  if not quarto.doc.is_format("html") then
    return pandoc.Null()
  end
  quarto.doc.add_html_dependency({
    name = "chartkit",
    version = "1.0.0",
    scripts = { "chartkit.js" },
    stylesheets = { "chartkit.css" },
  })
  local name = stringify_arg(kwargs["name"]) or stringify_arg(args[1])
  if name == nil then
    error("chartkit: {{< chart name >}} needs a chart name")
  end
  local spec = load_spec(name)
  local id = "chart-" .. name
  local blocks = pandoc.Blocks({})

  if not post_script_added then
    local script = pandoc.path.join({ post_dir(), "charts.js" })
    local file = io.open(script, "r")
    if file ~= nil then
      file:close()
      blocks:insert(pandoc.RawBlock("html", '<script src="charts.js"></script>'))
    end
    post_script_added = true
  end

  blocks:insert(markdown_div(spec.kicker or "Chart", "w-kicker"))
  blocks:insert(markdown_div(spec.title, "w-title", id .. "-title"))
  local sub = markdown_div(spec.sub, "w-sub")
  if sub then
    blocks:insert(sub)
  end
  local key = legend(spec)
  if key then
    blocks:insert(key)
  end
  blocks:insert(pandoc.Div({}, pandoc.Attr("", { "w-chart" }, {
    ["data-spec"] = quarto.json.encode(drawing_spec(spec)),
    style = string.format("--ck-h: %dpx", spec.height or 280),
  })))
  local numbers = data_table(spec)
  if numbers then
    blocks:insert(numbers)
  end
  local source = markdown_div(spec.source, "w-src")
  if source then
    blocks:insert(source)
  end
  return pandoc.Div(blocks, pandoc.Attr(id, { "chartkit", "widget" }, {
    role = "figure",
    ["aria-labelledby"] = id .. "-title",
  }))
end

return {
  ["chart"] = chart,
}
