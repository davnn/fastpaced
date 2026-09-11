module Lib.Metadata (articleFlags, metadataFlag, validateArticleMetadata) where

import Control.Monad (forM_, void)
import Data.Char (isSpace, toLower)
import Data.Time (Day, defaultTimeLocale, formatTime, parseTimeM)
import Hakyll (Compiler, Identifier, getMetadataField, toFilePath)

articleFlags :: [String]
articleFlags = ["mathematics", "centered"]

metadataFlag :: Identifier -> String -> Compiler Bool
metadataFlag identifier key = do
  value <- getMetadataField identifier key
  case fmap (map toLower) value of
    Nothing -> pure False
    Just "true" -> pure True
    Just "false" -> pure False
    _ -> fail (toFilePath identifier ++ ": " ++ key ++ " must be true or false")

requiredMetadata :: Identifier -> String -> Compiler String
requiredMetadata identifier key = do
  value <- getMetadataField identifier key
  case value of
    Just text | any (not . isSpace) text -> pure text
    _ -> fail (toFilePath identifier ++ ": missing required metadata field " ++ key)

-- Validate outside templates: template conditionals can hide field errors, and
-- Hakyll can fall back from an invalid published value to other date sources.
validateArticleMetadata :: Identifier -> Compiler ()
validateArticleMetadata identifier = do
  forM_ ["title", "author"] $ \key -> void (requiredMetadata identifier key)
  published <- requiredMetadata identifier "published"
  case parseTimeM True defaultTimeLocale "%Y-%m-%d" published :: Maybe Day of
    Just day | formatTime defaultTimeLocale "%Y-%m-%d" day == published -> pure ()
    _ -> fail (toFilePath identifier ++ ": published must be a valid YYYY-MM-DD date")
  forM_ articleFlags $ \key -> void (metadataFlag identifier key)
