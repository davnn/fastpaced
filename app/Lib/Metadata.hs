module Lib.Metadata (articleFlags, metadataFlag) where

import Data.Char (isSpace, toLower)
import Data.List (dropWhileEnd)
import Hakyll (Compiler, Identifier, getMetadataField)

articleFlags :: [String]
articleFlags = ["mathematics", "centered", "comments"]

-- Only an explicit true enables an optional flag. Comments remain enabled by
-- default, but an explicit false can disable them for an individual article.
metadataFlag :: Identifier -> String -> Compiler Bool
metadataFlag identifier key = do
  value <- getMetadataField identifier key
  pure $ maybe (key == "comments") ((== "true") . normalize) value
  where
    normalize = map toLower . dropWhileEnd isSpace . dropWhile isSpace
