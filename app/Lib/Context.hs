module Lib.Context (indexCtx, articleCtx, errorCtx, feedCtx) where

import Hakyll
import Lib.Configuration (siteRoot, siteTitle, siteDescription, siteSchema, katexBase)
import Lib.Metadata (articleFlags, metadataFlag)
import Lib.Url (routeUrl, absoluteUrl)

-- Escape plain text at HTML/XML boundaries, leaving rendered bodies and JSON
-- untouched. The feed renderer handles HTML descriptions separately.
escapedContext :: Context String -> Context String
escapedContext context = Context $ \key arguments item -> do
  value <- unContext context key arguments item
  pure $ case value of
    StringField text | key `elem` plainTextFields -> StringField (escapeHtml text)
    _ -> value
  where
    plainTextFields =
      [ "title", "author", "abstract", "defaultdescription", "layout"
      , "site", "url", "imageUrl", "katexBase"
      ]

-- A false flag must not fall through to defaultContext, where even the string
-- "false" counts as a present (and therefore true) field in $if(...)$.
booleanContext :: Context String -> Context String
booleanContext context = Context $ \key arguments item ->
  if key `elem` articleFlags
    then unContext (boolFieldM key (\entry -> metadataFlag (itemIdentifier entry) key)) key arguments item
    else unContext context key arguments item

siteCtx :: Context String
siteCtx =
  field "imageUrl" (\item -> do
    imagePath <- getMetadataField (itemIdentifier item) "image"
    url <- routeUrl (itemIdentifier item)
    maybe (pure $ siteRoot ++ "/assets/images/galaxy.jpg")
      (absoluteUrl (siteRoot ++ url)) imagePath) <>
  constField "katexBase" katexBase <>
  constField "siteSchema" siteSchema <>
  constField "site" siteRoot <>
  constField "defaultdescription" siteDescription <>
  field "url" (routeUrl . itemIdentifier) <>
  defaultContext

indexCtx :: [Item String] -> Context String
indexCtx posts = escapedContext $ booleanContext $
  listField "posts" articleCtx (pure posts) <>
  constField "title" siteTitle <>
  siteCtx

articleCtx :: Context String
articleCtx = escapedContext $ booleanContext $
  dateField "date" "%B %e, %Y" <>
  dateField "dateISO" "%Y-%m-%d" <>
  dateField "dateInt" "%Y%m%d" <>
  constField "layout" "article" <>
  siteCtx

errorCtx :: Context String
errorCtx = escapedContext $ booleanContext $
  constField "layout" "error" <>
  constField "title" "404: Not found" <>
  constField "body" "<p>:-(</p>" <>
  siteCtx

feedCtx :: Context String
-- Override raw publication metadata before defaultContext sees it: Atom needs
-- a full timestamp even when front matter contains only a calendar date.
feedCtx =
  bodyField "description" <>
  dateField "published" "%Y-%m-%dT%H:%M:%SZ" <>
  articleCtx
