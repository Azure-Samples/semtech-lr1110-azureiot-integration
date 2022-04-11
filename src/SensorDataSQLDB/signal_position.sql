CREATE TABLE [dbo].[signal_position]
(
	[id] [int] IDENTITY(1,1) NOT NULL,
	[devEUI][nvarchar](50) NOT NULL,
	[timestamp] [datetime] NOT NULL,
	[algorithm] [nvarchar](50) NULL,
	[latitude] [float] NOT NULL,
	[longitude] [float] NOT NULL,
	[longitude] [float] NULL,
 CONSTRAINT [PK_signal_position] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
