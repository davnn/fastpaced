module Lib.Context (indexCtx, articleCtx, errorCtx) where

import Hakyll
import System.FilePath (dropFileName)

site = "https://fastpaced.com"
title = "fastpaced | Data. Science. Code. Design. Thoughts."
description = "fastpaced is a blog about data science maintained by David Muhr. Learn about interesting new ideas and techniques."

-- Based on `urlField`
shortUrlField :: String -> Context a
shortUrlField key = field key $
    fmap (maybe mempty (toUrl . dropFileName)) . getRoute . itemIdentifier

-- Field that should exist in all contexts (for all pages)
extendedDefaultContext :: Context String
extendedDefaultContext =
  constField "site" site `mappend`
  constField "description" description `mappend`
  defaultContext

indexCtx :: [Item String] -> Context String
indexCtx posts =
  listField "posts" articleCtx (return posts) `mappend`
  constField "title" title `mappend`
  extendedDefaultContext

articleCtx :: Context String
articleCtx =
  dateField "date" "%B %e, %Y" `mappend`
  constField "layout" "article" `mappend`
  constField "comments" "true" `mappend`
  shortUrlField "url" `mappend`
  extendedDefaultContext

errorCtx :: Context String
errorCtx =
  constField "layout" "error" `mappend`
  constField "title" "404: Not found" `mappend`
  constField "body" "<p>:-(</p>" `mappend`
  extendedDefaultContext
