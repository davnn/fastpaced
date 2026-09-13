{-# LANGUAGE OverloadedStrings #-}

module Lib.Rules (siteRules) where

import Hakyll
import Lib.Configuration (feedConfig)
import Lib.Context (articleCtx, errorCtx, feedCtx, indexCtx)
import Lib.Pandoc (articleCompiler)

articlePattern :: Pattern
articlePattern = "articles/*/index.md"

bibliographyPattern :: Pattern
bibliographyPattern = "articles/*/*.bib"

siteRules :: Rules ()
siteRules = do
  -- Compile Index
  match "index.html" $ do
    route idRoute
    compile $ do
      posts <- recentFirst =<< loadAll articlePattern
      getResourceBody
        >>= applyAsTemplate (indexCtx posts)
        >>= loadAndApplyTemplate "templates/default.html" (indexCtx posts)

  -- Compile Styles
  match "assets/style.css" $
    compile $ compressCssCompiler >>= compileTemplateItem >>= makeItem

  -- Compile Bibliography
  match "assets/csl/*.csl" $ compile cslCompiler
  match bibliographyPattern $ compile biblioCompiler

  -- Compile Articles
  match articlePattern $ do
    route (setExtension "html")
    compile $ articleCompiler
      >>= loadAndApplyTemplate "templates/article.html" articleCtx
      >>= saveSnapshot "content" -- used for atom feed generation
      >>= loadAndApplyTemplate "templates/default.html" articleCtx

  -- Compile Files
  match ("CNAME" .||. "assets/images/**" .||. "assets/manifest/**" .||.
         ("articles/**" .&&. complement ("articles/**.md" .||. bibliographyPattern))) $ do
    route idRoute
    compile copyFileCompiler

  -- Compile Templates
  match "templates/**" $ compile templateBodyCompiler

  -- Compile 404
  create ["404.html"] $ do
    route idRoute
    compile $ makeItem ("" :: String)
      >>= loadAndApplyTemplate "templates/default.html" errorCtx

  -- Compile Feed
  create ["atom.xml"] $ do
    route idRoute
    compile $ do
      articles <- recentFirst =<< loadAllSnapshots articlePattern "content"
      renderAtom feedConfig feedCtx articles
