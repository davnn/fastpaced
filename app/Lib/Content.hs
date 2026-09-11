{-# LANGUAGE OverloadedStrings #-}

module Lib.Content
  ( articlePattern, bibliographyPattern, articleBibliographies, articleAttachments
  ) where

import Hakyll (Identifier, Pattern, complement, fromList, fromRegex, toFilePath, (.&&.), (.||.))
import System.FilePath.Posix (addTrailingPathSeparator, takeDirectory)

articlePattern, bibliographyPattern :: Pattern
articlePattern = "articles/*/index.md"
bibliographyPattern = "articles/*/*.bib"

-- A source directory is literal data, never a user-supplied glob or regex.
-- Keep this a pattern (not a list of existing files) so newly added resources match.
articleDirectory :: Identifier -> Pattern
articleDirectory identifier = fromRegex ("^" ++ concatMap escape directory)
  where
    directory = addTrailingPathSeparator (takeDirectory (toFilePath identifier))
    escape character
      | character `elem` ("\\.^$|?*+()[]{}" :: String) = ['\\', character]
      | otherwise = [character]

articleBibliographies :: Identifier -> Pattern
articleBibliographies identifier = articleDirectory identifier .&&. bibliographyPattern

articleAttachments :: [Identifier] -> Pattern
articleAttachments articles =
  foldr (.||.) (fromList []) (map articleDirectory articles) .&&.
  complement ("articles/**.md" .||. "articles/**.bib" .||. "articles/*/index.html")
