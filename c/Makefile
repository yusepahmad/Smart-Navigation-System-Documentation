CC      = gcc
CXX     = g++
CFLAGS  = -O2 -lm
CXXFLAGS = -std=c++17 -O2

.PHONY: all clean c cpp

all: c cpp

c: cli_app

cpp: cli_app_cpp

cli_app: cli_app.c
	$(CC) $(CFLAGS) -o $@ $<

cli_app_cpp: cli_app.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	rm -f cli_app cli_app_cpp
