module Lib.Context (indexCtx, articleCtx, errorCtx, feedCtx) where

import Hakyll
import Lib.Metadata (articleFlags, metadataFlag)
import Lib.Url (routeUrl, absoluteUrl)
import Lib.Configuration (siteRoot, siteTitle, siteDescription, siteSchema, katexBase)

-- Escape plain-text metadata at HTML/XML rendering boundaries. Article bodies
-- stay HTML; feed descriptions are handled separately by the feed renderer.
escapedContext :: Context String -> Context String
escapedContext context = Context $ \key arguments item -> do
  value <- unContext context key arguments item
  pure $ case value of
    StringField text | key `elem` ["title", "author", "abstract", "defaultdescription", "layout", "url", "imageUrl"] ->
      StringField (escapeHtml text)
    _ -> value

-- Intercept boolean keys before metadata fallback: a present "false" is false.
booleanContext :: Context String -> Context String
booleanContext context = Context $ \key arguments item ->
  if key `elem` articleFlags
    then unContext (boolFieldM key (enabled key)) key arguments item
    else unContext context key arguments item
  where
    enabled key item = metadataFlag (itemIdentifier item) key

siteCtx :: Context String
siteCtx =
  field "imageUrl" (\item -> do
    imagePath <- getMetadataField (itemIdentifier item) "image"
    url <- routeUrl (itemIdentifier item)
    let base = siteRoot ++ url
    pure $ maybe (siteRoot ++ "/assets/images/galaxy.jpg") (absoluteUrl base) imagePath) <>
  constField "katexBase" katexBase <>
  constField "siteSchema" siteSchema <>
  constField "site" siteRoot <>
  constField "defaultdescription" siteDescription <>
  field "url" (routeUrl . itemIdentifier) <>
  defaultContext

indexCtx :: [Item String] -> Context String
indexCtx posts = escapedContext $
  listField "posts" articleCtx (pure posts) <>
  constField "title" siteTitle <>
  siteCtx

articleCtx :: Context String
articleCtx = escapedContext $ booleanContext $
  dateField "date" "%B %e, %Y" <>
  dateField "dateISO" "%Y-%m-%d" <>
  constField "layout" "article" <>
  constField "comments" "true" <>
  siteCtx

errorCtx :: Context String
errorCtx = escapedContext $
  constField "layout" "error" <>
  constField "title" "404: Not found" <>
  constField "body" "<p>:-(</p>" <>
  siteCtx

-- Descriptions are rendered as feed HTML; metadata is already XML-safe.
feedCtx :: Context String
feedCtx = bodyField "description" <> articleCtx
