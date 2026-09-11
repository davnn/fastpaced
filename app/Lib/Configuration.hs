{-# LANGUAGE OverloadedStrings #-}

module Lib.Configuration
  ( siteRoot, siteTitle, siteDescription
  , citationStyle, contentSnapshot, feedConfig, siteSchema, katexBase
  ) where

import Data.Aeson (encode, object, (.=))
import qualified Data.Text.Lazy as Text
import Data.Text.Lazy.Encoding (decodeUtf8)
import Hakyll (FeedConfiguration (..), Identifier)

siteRoot, siteTitle, siteDescription :: String
siteRoot = "https://fastpaced.com"
siteTitle = "Data. Science. Code. Design. Thoughts. - fastpaced"
siteDescription = "A research-oriented blog about data, engineering and other interesting topics. Maintained by David Muhr, a machine learning and software engineering leader in Austria."

-- CSS and JavaScript must use the same release.
katexBase :: String
katexBase = "https://cdn.jsdelivr.net/npm/katex@0.18.7/dist/"

citationStyle :: Identifier
citationStyle = "assets/csl/chicago-author-date.csl"

contentSnapshot :: String
contentSnapshot = "content"

feedConfig :: FeedConfiguration
feedConfig = FeedConfiguration
  { feedTitle = "fastpaced.com"
  , feedDescription = "Data. Science. Code. Design. Thoughts."
  , feedAuthorName = "David Muhr"
  , feedAuthorEmail = "muhrdavid+atom@gmail.com"
  , feedRoot = siteRoot
  }

siteSchema :: String
siteSchema = concatMap escapeScript (Text.unpack (decodeUtf8 (encode schema)))
  where
    schema = object
      [ "@context" .= ("https://schema.org" :: String)
      , "@type" .= ("Blog" :: String)
      , "@id" .= siteRoot
      , "name" .= ("fastpaced" :: String)
      , "description" .= siteDescription
      , "author" .= object ["@type" .= ("Person" :: String), "name" .= feedAuthorName feedConfig]
      , "inLanguage" .= ("en-US" :: String)
      ]
    escapeScript '<' = "\\u003c"
    escapeScript character = [character]
