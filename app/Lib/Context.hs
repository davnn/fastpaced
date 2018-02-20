module Lib.Context (indexCtx, postCtx, errorCtx) where

import Hakyll
import System.FilePath (takeDirectory)

site = "https://curious.observer"
title = "Curious Observer | Data. Science. Code. Design. Thoughts."

-- Based on `urlField`
shortUrlField :: String -> Context a
shortUrlField key = field key $
    fmap (maybe mempty (toUrl . takeDirectory)) . getRoute . itemIdentifier

-- Field that should be in all contexts
extendedDefaultContext :: Context String
extendedDefaultContext =
  constField "site" site `mappend`
  defaultContext

indexCtx :: [Item String] -> Context String
indexCtx posts =
  listField "posts" postCtx (return posts) `mappend`
  constField "title" title `mappend`
  extendedDefaultContext

postCtx :: Context String
postCtx =
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
