import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import agents_router


def parse_args():
	parser = argparse.ArgumentParser(
		description="Run the Via Ludus webservice."
	)

	parser.add_argument(
		"--host",
		default="127.0.0.1",
		help="host address (default: %(default)s)"
	)

	parser.add_argument(
		"--port",
		type=int,
		default=8080,
		help="port number (default: %(default)s)"
	)

	parser.add_argument(
		"--frontend",
		type=Path,
		help="frontend directory"
	)

	return vars(parser.parse_args())


def main(host, port, frontend):
	app = FastAPI(
		title="Via Ludus API",
	)

	#app.add_middleware(
	#	CORSMiddleware,
	#	allow_origins=["*"],
	#	allow_methods=["*"],
	#	allow_headers=["*"],
	#)

	app.include_router(
		agents_router,
		prefix="/api",
	)

	if frontend is not None:
		app.mount(
			"/",
			StaticFiles(
				directory=frontend,
				html=True,
			),
			name="frontend",
		)

	uvicorn.run(
		app,
		host=host,
		port=port,
	)


if __name__ == "__main__":
	main(**parse_args())

