module Lib.Url (routeUrl, absoluteUrl) where

import Hakyll (Compiler, Identifier, getRoute, toUrl)
import Network.URI (escapeURIString, isAllowedInURI, parseURI, parseURIReference, relativeTo)
import System.FilePath.Posix (dropFileName, takeFileName)

-- URLs use forward slashes on every platform. Only index pages have directory URLs.
routeUrl :: Identifier -> Compiler String
routeUrl identifier = do
  route <- getRoute identifier
  case route of
    Nothing -> fail $ "No route for " ++ show identifier
    Just path ->
      let url = toUrl path
      in pure $ if takeFileName url == "index.html" then dropFileName url else url

-- Resolve relative paths, root-relative paths, and absolute URLs with URI rules,
-- including dot segments and query strings, rather than filesystem concatenation.
absoluteUrl :: String -> String -> Compiler String
absoluteUrl base reference =
  case (parseURI base, parseURIReference (escapeURIString isAllowedInURI reference)) of
    (Just baseUri, Just referenceUri) -> pure $ show (referenceUri `relativeTo` baseUri)
    _ -> fail $ "Cannot resolve URL " ++ show reference ++ " against " ++ show base
