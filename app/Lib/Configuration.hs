module Lib.Configuration where

import Hakyll

feedConfig :: FeedConfiguration
feedConfig = FeedConfiguration {
        feedTitle       = "fastpaced.com",
        feedDescription = "Data. Science. Code. Design. Thoughts.",
        feedAuthorName  = "David Muhr",
        feedAuthorEmail = "dmuhr@hotmail.com",
        feedRoot        = "https://fastpaced.com"
      }
