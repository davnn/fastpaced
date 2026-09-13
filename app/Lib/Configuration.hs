{-# LANGUAGE OverloadedStrings #-}

module Lib.Configuration (feedConfig, siteRoot, siteTitle, siteDescription, siteSchema, katexBase) where

import Data.Aeson (encode, object, (.=))
import qualified Data.ByteString.Lazy as ByteString
import qualified Data.Text as Text
import Data.Text.Encoding (decodeUtf8)
import Hakyll (FeedConfiguration (..))

siteRoot, siteTitle, siteDescription :: String
siteRoot = "https://fastpaced.com"
siteTitle = "Data. Science. Code. Design. Thoughts. - fastpaced"
siteDescription = "A research-oriented blog about data, engineering and other interesting topics. Maintained by David Muhr, a machine learning and software engineering leader in Austria."

feedConfig :: FeedConfiguration
feedConfig = FeedConfiguration
  { feedTitle = "fastpaced.com"
  , feedDescription = "Data. Science. Code. Design. Thoughts."
  , feedAuthorName = "David Muhr"
  , feedAuthorEmail = "muhrdavid+atom@gmail.com"
  , feedRoot = siteRoot
  }

katexBase :: String
katexBase = "https://cdn.jsdelivr.net/npm/katex@0.18.7/dist"

-- Serialize JSON rather than interpolating HTML-escaped fields into JavaScript.
-- Escape HTML delimiters as JSON escapes so script elements cannot close early.
siteSchema :: String
siteSchema = concatMap scriptEscape . Text.unpack . decodeUtf8 . ByteString.toStrict . encode $ object
  [ "@context" .= ("https://schema.org" :: String)
  , "@type" .= ("Blog" :: String)
  , "@id" .= siteRoot
  , "name" .= ("fastpaced" :: String)
  , "description" .= siteDescription
  , "author" .= author
  , "creator" .= author
  , "publisher" .= author
  , "inLanguage" .= ("en-US" :: String)
  ]
  where
    author = object ["@type" .= ("Person" :: String), "name" .= feedAuthorName feedConfig]
    scriptEscape '<' = "\\u003c"
    scriptEscape '>' = "\\u003e"
    scriptEscape '&' = "\\u0026"
    scriptEscape c = [c]
