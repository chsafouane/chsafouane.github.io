-- Shortcodes for figures built with tools/figkit.
--
--   {{< fig name "Caption in *Markdown*" >}}
--   {{< stepper name "Caption shown under every step" >}}
--
-- Both read assets/figures/<name>.json next to the post (written by
-- `uv run figkit build`) and emit a light and a dark SVG; Quarto's
-- .light-content / .dark-content rules show the one that matches the page.
-- The images carry the `lightbox` class, so Quarto's lightbox (glightbox)
-- lets readers open a figure full size, which matters on phones.

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

local function arg(args, kwargs, index, key)
  return stringify_arg(kwargs[key]) or stringify_arg(args[index])
end

local function load_manifest(name, kind)
  local dir = pandoc.path.directory(quarto.doc.input_file)
  local path = pandoc.path.join({ dir, "assets", "figures", name .. ".json" })
  local file = io.open(path, "r")
  if file == nil then
    error("figkit: no figure manifest at " .. path .. " (run `uv run figkit build`)")
  end
  local manifest = quarto.json.decode(file:read("a"))
  file:close()
  if manifest.kind ~= kind then
    error("figkit: '" .. name .. "' is a " .. tostring(manifest.kind) .. ", use the matching shortcode")
  end
  return manifest
end

-- The images of one drawing, as inline elements: a light and a dark SVG for
-- figures drawn with figkit, or one PNG for imported (Keynote) figures, which
-- the site shows on a white plate in dark mode.
local function images(stem, manifest, alt, lazy)
  local inlines = pandoc.Inlines({})
  if manifest.format == "png" then
    local attributes = {
      width = tostring(manifest.width),
      height = tostring(manifest.height),
      decoding = "async",
      ["fig-alt"] = alt,
    }
    if lazy then
      attributes.loading = "lazy"
    end
    local attr = pandoc.Attr("", { "figkit-raster", "lightbox" }, attributes)
    inlines:insert(pandoc.Image(pandoc.Inlines({}), "assets/figures/" .. stem .. ".png", "", attr))
    return inlines
  end
  for _, mode in ipairs({ "light", "dark" }) do
    -- Alt text goes in fig-alt rather than the caption, so Quarto's lightbox
    -- does not also turn it into a (long) link title.
    local attributes = {
      width = tostring(manifest.width),
      height = tostring(manifest.height),
      decoding = "async",
      ["fig-alt"] = alt,
    }
    if lazy then
      attributes.loading = "lazy"
    end
    local src = "assets/figures/" .. stem .. "-" .. mode .. ".svg"
    local attr = pandoc.Attr("", { "figkit-img", mode .. "-content", "lightbox" }, attributes)
    inlines:insert(pandoc.Image(pandoc.Inlines({}), src, "", attr))
  end
  return inlines
end

local function caption_block(caption, class)
  if caption == nil then
    return nil
  end
  return pandoc.Div(pandoc.read(caption, "markdown").blocks, pandoc.Attr("", { class }))
end

local function wrapper(classes, manifest, id)
  return pandoc.Attr(id or "", classes, {
    role = "figure",
    style = string.format("--figkit-width: %dpx", manifest.width),
  })
end

local function fig(args, kwargs)
  if not quarto.doc.is_format("html") then
    return pandoc.Null()
  end
  local name = arg(args, kwargs, 1, "name")
  local manifest = load_manifest(name, "figure")
  local blocks = pandoc.Blocks({ pandoc.Plain(images(name, manifest, manifest.alt, true)) })
  local caption = caption_block(arg(args, kwargs, 2, "caption"), "figkit-caption")
  if caption then
    blocks:insert(caption)
  end
  return pandoc.Div(blocks, wrapper({ "figkit" }, manifest, arg(args, kwargs, 3, "id")))
end

local function stepper(args, kwargs)
  if not quarto.doc.is_format("html") then
    return pandoc.Null()
  end
  quarto.doc.add_html_dependency({
    name = "figkit-stepper",
    version = "1.0.0",
    scripts = { "stepper.js" },
  })
  local name = arg(args, kwargs, 1, "name")
  local manifest = load_manifest(name, "stepper")
  local count = #manifest.steps
  local frames = pandoc.Blocks({})
  for step, info in ipairs(manifest.steps) do
    local alt = string.format("%s Step %d of %d: %s", manifest.alt, step, count, info.caption)
    local label = pandoc.read(info.caption, "markdown").blocks[1]
    local caption_inlines = pandoc.Inlines({
      pandoc.Span(pandoc.Inlines(tostring(step)), pandoc.Attr("", { "figkit-step-number" })),
      pandoc.Space(),
    })
    if label ~= nil then
      caption_inlines:extend(label.content)
    end
    frames:insert(pandoc.Div({
      pandoc.Plain(images(name .. "-" .. step, manifest, alt, step > 1)),
      pandoc.Div({ pandoc.Plain(caption_inlines) }, pandoc.Attr("", { "figkit-step-caption" })),
    }, pandoc.Attr("", { "figkit-frame" }, { ["data-step"] = tostring(step) })))
  end
  local blocks = pandoc.Blocks({
    pandoc.Div(frames, pandoc.Attr("", { "figkit-frames" })),
    pandoc.RawBlock("html", string.format([[
<div class="figkit-controls" hidden>
<button type="button" class="figkit-prev" aria-label="Previous step"><i class="bi bi-arrow-left" aria-hidden="true"></i></button>
<span class="figkit-counter" aria-live="polite">1 / %d</span>
<button type="button" class="figkit-next" aria-label="Next step"><i class="bi bi-arrow-right" aria-hidden="true"></i></button>
<button type="button" class="figkit-play" aria-label="Play all steps"><i class="bi bi-play-fill" aria-hidden="true"></i></button>
</div>]], count)),
  })
  local caption = caption_block(arg(args, kwargs, 2, "caption"), "figkit-caption")
  if caption then
    blocks:insert(caption)
  end
  return pandoc.Div(blocks, wrapper({ "figkit", "figkit-stepper" }, manifest, arg(args, kwargs, 3, "id")))
end

return {
  ["fig"] = fig,
  ["stepper"] = stepper,
}
