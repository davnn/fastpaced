module Lib.Configuration where

import Hakyll

feedConfig :: FeedConfiguration
feedConfig = FeedConfiguration {
        feedTitle       = "curious.observer",
        feedDescription = "Data. Science. Code. Design. Thoughts.",
        feedAuthorName  = "David Muhr",
        feedAuthorEmail = "dmuhr@hotmail.com",
        feedRoot        = "https://curious.observer"
      }
