module Lib.Context (indexCtx, articleCtx, errorCtx) where

import Hakyll
import System.FilePath (dropFileName)

site = "https://fastpaced.com"
title = "Data. Science. Code. Design. Thoughts. - fastpaced"
description = "A research-oriented blog about data, engineering and other interesting topics. Maintained by David Muhr, a machine learning doctoral student, currently working and living in beautiful Austria."

-- Based on `urlField`
shortUrlField :: String -> Context a
shortUrlField key = field key $
    fmap (maybe mempty (toUrl . dropFileName)) . getRoute . itemIdentifier

-- Field that should exist in all contexts (for all pages)
extendedDefaultContext :: Context String
extendedDefaultContext =
  constField "site" site <>
  constField "defaultdescription" description <>
  defaultContext

indexCtx :: [Item String] -> Context String
indexCtx posts =
  listField "posts" articleCtx (return posts) <>
  constField "title" title <>
  extendedDefaultContext

articleCtx :: Context String
articleCtx =
  dateField "date" "%B %e, %Y" <>
  dateField "dateInt" "%Y%m%d" <>
  constField "layout" "article" <>
  constField "comments" "true" <>
  shortUrlField "url" <>
  extendedDefaultContext

errorCtx :: Context String
errorCtx =
  constField "layout" "error" <>
  constField "title" "404: Not found" <>
  constField "body" "<p>:-(</p>" <>
  extendedDefaultContext
