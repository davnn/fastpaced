module Lib.Configuration where

import Hakyll

feedConfig :: FeedConfiguration
feedConfig = FeedConfiguration {
        feedTitle       = "fastpaced.com",
        feedDescription = "Data. Science. Code. Design. Thoughts.",
        feedAuthorName  = "David Muhr",
        feedAuthorEmail = "muhrdavid+atom@gmail.com",
        feedRoot        = "https://fastpaced.com"
      }
