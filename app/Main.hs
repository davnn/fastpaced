{-# LANGUAGE OverloadedStrings #-}
import Data.Monoid (mappend)
import Data.Traversable (forM)

import Hakyll
import Hakyll.Web.Sass (sassCompiler)

import Lib.Pandoc (pandocCompiler')
import Lib.Configuration (feedConfig)
import Lib.Context (indexCtx, articleCtx, errorCtx)

-- The path to our articles in Hakyll's pattern notation
articlePath = "articles/*/*.md"

--------------------------------------------------------------------------------
main :: IO ()
main = hakyll $ do
  -- Compile Index
  match "index.html" $ do
    route idRoute
    compile $ do
      posts <- recentFirst =<< loadAll articlePath
      getResourceBody
        >>= applyAsTemplate (indexCtx posts)
        >>= loadAndApplyTemplate "templates/default.html" (indexCtx posts)

  -- Compile Styles
  match "assets/styles/main.scss" $ do
    -- Compress the CSS and transform to Template
    let compressToTemplate = fmap (readTemplate . compressCss)
    compile (compressToTemplate <$> sassCompiler)

  -- Compile Bibliography
  match "assets/csl/*.csl" $ compile cslCompiler
  match "articles/*/*.bib" $ compile biblioCompiler

  -- Compile Articles
  match articlePath $ do
    route (setExtension ".html")
    compile $ pandocCompiler'
      >>= saveSnapshot "raw" -- used for teaser generation
      >>= loadAndApplyTemplate "templates/article.html" articleCtx
      >>= saveSnapshot "content" -- used for atom feed generation
      >>= loadAndApplyTemplate "templates/default.html" articleCtx

  -- Compile Files
  match ("assets/images/**" .||. "assets/manifest/**" .||. "articles/**") $ do
    route idRoute
    compile copyFileCompiler

  -- Compile Templates
  match "templates/**" $ compile templateBodyCompiler

  -- Compile 404
  create ["404.html"] $ do
    route idRoute
    compile $ makeItem "Error" -- this does nothing but create an empty Item
      >>= loadAndApplyTemplate "templates/default.html" errorCtx
      >>= relativizeUrls

  -- Compile Feed
  create ["atom.xml"] $ do
    route idRoute
    compile $ do
      let feedCtx = articleCtx `mappend` bodyField "description"
      articles <- recentFirst =<< loadAllSnapshots articlePath "content"
      renderAtom feedConfig feedCtx articles
